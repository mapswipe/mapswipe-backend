import contextlib
import csv
import logging
import re
import time
import typing
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from cachetools import LRUCache, cached
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandParser
from django.db import models
from django.db.models.functions import Trim
from django.db.utils import IntegrityError
from django.utils import timezone
from ulid import ULID

from apps.common.models import AssetTypeEnum
from apps.community_dashboard.models import (
    AggregatedTracking,
    AggregatedTrackingTypeEnum,
    AggregatedUserGroupStatData,
    AggregatedUserStatData,
)
from apps.contributor.models import (
    ContributorTeam,
    ContributorUser,
    ContributorUserGroup,
    ContributorUserGroupMembership,
)
from apps.existing_database import models as existing_db_models
from apps.project.models import (
    Organization,
    Project,
    ProjectAsset,
    ProjectAssetExportTypeEnum,
    ProjectTypeEnum,
)
from apps.user.models import User
from main.bulk_managers import BulkCreateManager
from main.config import Config

FH = Config.FIREBASE_HELPER

logger = logging.getLogger(__name__)


def sanitize_name(text: str) -> str:
    return " ".join(text.replace("\n", " ").strip().split())


def parse_datetime(
    dt: datetime | None,
    empty_fallback: typing.Callable[[], datetime | None] | datetime | None = timezone.now,
) -> datetime | None:
    if dt is None:
        if callable(empty_fallback):
            return empty_fallback()
        return empty_fallback
    if dt.tzinfo is not None:
        return dt
    return timezone.make_aware(dt)


def parse_existing_project_type(project_type: int):
    if project_type == 1:
        return ProjectTypeEnum.FIND
    if project_type == 2:
        return ProjectTypeEnum.VALIDATE
    if project_type == 10:
        return ProjectTypeEnum.VALIDATE_IMAGE
    if project_type == 3:
        return ProjectTypeEnum.COMPARE
    if project_type == 4:
        return ProjectTypeEnum.COMPLETENESS

    # TODO(thenav56): THIS IS WRONG
    if project_type == 7:
        return ProjectTypeEnum.FIND

    raise Exception(f"Existing project_type: {project_type} is not mappable to this system")


def before_after_count[**P, R](
    Models: type[models.Model] | list[type[models.Model]],
) -> typing.Callable[
    [typing.Callable[typing.Concatenate["Command", P], R]],
    typing.Callable[typing.Concatenate["Command", P], R],
]:
    def decorator(
        func: typing.Callable[typing.Concatenate["Command", P], R],
    ) -> typing.Callable[typing.Concatenate["Command", P], R]:
        @wraps(func)
        def wrapper(
            self: "Command",
            /,
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R:
            start_time = time.time()
            model_count_map = defaultdict(dict)

            Models_ = Models if isinstance(Models, list) else [Models]

            g_prefix = ",".join([m.__name__ for m in Models_])
            for Model_ in Models_:
                model_count_map[Model_]["before"] = Model_.objects.count()

            self.stdout.write(f"# {g_prefix} " + "#" * 50)

            result = func(self, *args, **kwargs)

            for Model_ in Models_:
                model_count_map[Model_]["after"] = Model_.objects.count()

            for Model_ in Models_:
                before_count = model_count_map[Model_]["before"]
                after_count = model_count_map[Model_]["after"]
                self.stdout.write(
                    self.style.WARNING(
                        f"{Model_.__name__} - Diff Count: ({before_count} -> {after_count}) = +{after_count - before_count}",
                    ),
                )

            runtime_diff = timedelta(seconds=time.time() - start_time)
            self.stdout.write(
                self.style.SUCCESS(
                    f"End (runtime: {runtime_diff})",
                ),
            )

            return result

        return wrapper

    return decorator


@cached(cache=LRUCache(maxsize=1000))
def get_contributor_user_id_by_firebase_id(firebase_id: str) -> int:
    return ContributorUser.objects.get(firebase_id=firebase_id).pk


@cached(cache=LRUCache(maxsize=1000))
def get_project_id_by_old_id(old_id: str) -> int:
    return Project.objects.get(old_id=old_id).pk


@cached(cache=LRUCache(maxsize=1000))
def get_user_by_contributor_user_firebase_id(
    firebase_id: str | None,
    *,
    fallback: User,
) -> int:
    if firebase_id is None:
        return fallback.pk

    return User.objects.get_or_create(
        contributor_user_id=get_contributor_user_id_by_firebase_id(firebase_id),
        defaults=dict(
            # XXX: Email is required but we don't have emails
            email=f"fixup-{firebase_id}@mapswipe.org",
        ),
    )[0].pk


@cached(cache=LRUCache(maxsize=1000))
def get_contributor_user_group_by_old_id(old_id: str) -> int:
    return ContributorUserGroup.objects.get(old_id=old_id).pk


@cached(cache=LRUCache(maxsize=1000))
def get_contributor_user_group_id_by_old_id(old_id: str) -> int:
    return ContributorUserGroup.objects.get(old_id=old_id).pk


@cached(cache=LRUCache(maxsize=1000))
def get_organization_by_name(name: str | None) -> Organization:
    name_ = sanitize_name(name or "")
    if not name_:
        return Organization.objects.get(name__iexact="Unknown")
    try:
        return Organization.objects.annotate(
            # XXX: Not same as sanitize_name, but it is working for now
            trimmed_name=Trim("name"),
        ).get(trimmed_name__iexact=name_)
    except Organization.DoesNotExist:
        logger.error("Organization name not found: <%s>", name_)
        raise


# TODO(thenav56): Cache?
def generate_django_content_file_from_url(
    absolute_path: str,
) -> ContentFile | None:
    file_url = urljoin(Config.EXISTING_SYSTEM_API.geturl(), absolute_path)

    response = None
    try:
        response = httpx.get(file_url, verify=not Config.EXISTING_SYSTEM_API_INSECURE)
        response.raise_for_status()
    except httpx.HTTPStatusError:
        logger.warning(
            "Failed to download: %s. (status code: %s)",
            file_url,
            response and response.status_code,
        )
        return None

    # Extract filename from URL
    parsed_url = urlparse(file_url)
    filename = Path(parsed_url.path).name or "downloaded_file"

    # Wrap the content in Django ContentFile
    return ContentFile(response.content, name=filename)


def parse_project_name(
    pre_parsed_map: dict[str, tuple[str, str, int, str]],
    name: str | None,
) -> tuple[str, str, int, str] | None:
    if not name:
        logger.error("Failed to parse project_name: Empty name")
        return None

    entry = sanitize_name(name)

    parsed_value = pre_parsed_map.get(name, pre_parsed_map.get(entry))
    if parsed_value is not None:
        return parsed_value

    logger.warning(
        "Failed to parse project_name: Not in pre-parsed map: %s (sanitized: %s)",
        name,
        entry,
    )

    # Regex pattern to match the main structure
    match = re.match(r"(.+?)\s*-\s*(.+?)\s*\((\d+)\)\s*(.*)", name.strip())

    if match:
        topic = match.group(1).strip()
        region = match.group(2).strip()
        number = int(match.group(3).strip())
        request_organization = match.group(4).strip()
    else:
        # Handle names without full match
        # Try looser match: Look for last (number)
        loose_match = re.search(r"\((\d+)\)", name)
        if loose_match:
            number = int(loose_match.group(1))
            prefix = name[: loose_match.start()].strip()
            suffix = name[loose_match.end() :].strip()

            # Try to find last dash for splitting topic and region
            dash_parts = prefix.split(" - ")
            if len(dash_parts) > 1:
                topic = dash_parts[0].strip()
                region = dash_parts[1].strip()
            else:
                topic = prefix.strip()
                region = ""
            request_organization = suffix
        else:
            raise Exception(f"Failed to parse project name: {name}")

    return topic, region, number, request_organization


def create_project(
    *,
    client_id: str,
    topic: str,
    region: str,
    project_number: int,
    existing_project: existing_db_models.Project,
    requesting_organization: str,
    bot_user: User,
):
    try:
        assert existing_project.project_type is not None, "Project type should be defined"
        project_metadata = dict(
            topic=topic,
            region=region,
            project_number=project_number,
            centroid=existing_project.geom and existing_project.geom.centroid,
            project_type=parse_existing_project_type(existing_project.project_type),
            requesting_organization=get_organization_by_name(requesting_organization),
            created_by_id=get_user_by_contributor_user_firebase_id(existing_project.created_by, fallback=bot_user),
            modified_by_id=get_user_by_contributor_user_firebase_id(existing_project.created_by, fallback=bot_user),
        )

        return Project.objects.update_or_create(
            old_id=existing_project.project_id,
            create_defaults=dict(
                client_id=client_id,
                firebase_id=existing_project.project_id,
                **project_metadata,
            ),
            defaults=project_metadata,
        )
    except IntegrityError as e:
        if not str(e).startswith('duplicate key value violates unique constraint "unique_project_name"'):
            raise

        # NOTE: Trying again with project_number + 1
        return create_project(
            client_id=client_id,
            topic=topic,
            region=region,
            project_number=project_number + 1,
            existing_project=existing_project,
            requesting_organization=requesting_organization,
            bot_user=bot_user,
        )


def get_api_url_by_project_export_type(export_type: ProjectAssetExportTypeEnum, project_old_id: str):
    if export_type == ProjectAssetExportTypeEnum.AGGREGATED_RESULTS:
        return f"/api/agg_results/agg_results_{project_old_id}.csv.gz"
    if export_type == ProjectAssetExportTypeEnum.AGGREGATED_RESULTS_WITH_GEOMETRY:
        return f"/api/agg_results/agg_results_{project_old_id}_geom.geojson.gz"
    if export_type == ProjectAssetExportTypeEnum.GROUPS:
        return f"/api/groups/groups_{project_old_id}.csv.gz"
    if export_type == ProjectAssetExportTypeEnum.HISTORY:
        return f"/api/history/history_{project_old_id}.csv"
    if export_type == ProjectAssetExportTypeEnum.RESULTS:
        return f"/api/results/results_{project_old_id}.csv.gz"
    if export_type == ProjectAssetExportTypeEnum.TASKS:
        return f"/api/tasks/tasks_{project_old_id}.csv.gz"
    if export_type == ProjectAssetExportTypeEnum.USERS:
        return f"/api/users/users_{project_old_id}.csv.gz"
    if export_type == ProjectAssetExportTypeEnum.AREA_OF_INTEREST:
        return f"/api/project_geometries/project_geom_{project_old_id}.geojson"
    if export_type == ProjectAssetExportTypeEnum.MODERATE_TO_HIGH_AGREEMENT_YES_MAYBE_GEOMETRIES:
        return f"/api/yes_maybe/yes_maybe_{project_old_id}.geojson"
    if export_type == ProjectAssetExportTypeEnum.HOT_TASKING_MANAGER_GEOMETRIES:
        return f"/api/hot_tm/hot_tm_{project_old_id}.geojson"
    typing.assert_never(export_type)


def create_project_assets(project: Project):
    # NOTE: old_id must be defined when loading data from existing database
    assert project.old_id is not None, "Project old id must be defined"

    common_export_types = [
        # Common
        ProjectAssetExportTypeEnum.AGGREGATED_RESULTS,
        ProjectAssetExportTypeEnum.AGGREGATED_RESULTS_WITH_GEOMETRY,
        ProjectAssetExportTypeEnum.GROUPS,
        ProjectAssetExportTypeEnum.HISTORY,
        ProjectAssetExportTypeEnum.RESULTS,
        ProjectAssetExportTypeEnum.TASKS,
        ProjectAssetExportTypeEnum.USERS,
        ProjectAssetExportTypeEnum.AREA_OF_INTEREST,
    ]

    export_type_by_project_types = {
        ProjectTypeEnum.FIND: [
            *common_export_types,
            ProjectAssetExportTypeEnum.MODERATE_TO_HIGH_AGREEMENT_YES_MAYBE_GEOMETRIES,
            ProjectAssetExportTypeEnum.HOT_TASKING_MANAGER_GEOMETRIES,
        ],
        ProjectTypeEnum.COMPARE: [
            *common_export_types,
            ProjectAssetExportTypeEnum.MODERATE_TO_HIGH_AGREEMENT_YES_MAYBE_GEOMETRIES,
            ProjectAssetExportTypeEnum.HOT_TASKING_MANAGER_GEOMETRIES,
        ],
    }

    for export_type in export_type_by_project_types.get(project.project_type_enum, common_export_types):
        if ProjectAsset.objects.filter(project=project, export_type=export_type).exists():
            continue

        file_url = get_api_url_by_project_export_type(export_type, project.old_id)
        content_file = generate_django_content_file_from_url(file_url)

        if content_file is None:
            continue

        # Attaching project exports
        ProjectAsset.objects.create(
            project=project,
            client_id=str(ULID()),
            type=AssetTypeEnum.EXPORT,
            export_type=export_type,
            file=content_file,
            mimetype=ProjectAssetExportTypeEnum.get_mimetype(export_type),
            file_size=content_file.size,
            created_by=project.created_by,
            modified_by=project.modified_by,
        )


class Command(BaseCommand):
    help = "Create schema.graphql file"

    def __init__(self, *args: typing.Any, **kwargs: typing.Any):
        super().__init__(*args, **kwargs)
        self.bulk_create_mgr = BulkCreateManager()
        self.bot_user = User.get_bot_user()
        self._pre_parsed_project_names: dict[str, tuple[str, str, int, str]] | None = None

    @before_after_count(Organization)
    def handle_organization(self):
        # TODO(thenav56): pull from firebase: createdBy,createdAt,description
        existing_organization_names_qs = existing_db_models.Project.objects.values_list(
            "organization_name",
            flat=True,
        ).distinct()

        current_organizations_set = {sanitize_name(name) for name in Organization.objects.values_list("name", flat=True)}

        unknown_organization, unknown_created = Organization.objects.get_or_create(
            name="Unknown",
            defaults=dict(
                client_id=str(ULID()),
                created_by=self.bot_user,
                modified_by=self.bot_user,
            ),
        )

        if unknown_created:
            logger.info("New: %s", unknown_organization)

        existing_organization_names = set(
            [
                *[sanitize_name(name_) for name_ in existing_organization_names_qs],
                *[organization_name for _, _, _, organization_name in self._get_pre_parsed_project_names().values()],
            ],
        )

        total_existing = len(existing_organization_names)

        for i, name in enumerate(existing_organization_names, start=1):
            self.stdout.write(f"\rProcessing {i}/{total_existing}", ending="")

            name_ = sanitize_name(name)
            if not name_ or name_ in current_organizations_set:
                continue

            logger.info("New: %s", name)

            self.bulk_create_mgr.add(
                Organization(
                    name=name,
                    client_id=str(ULID()),
                    created_by=self.bot_user,
                    modified_by=self.bot_user,
                ),
            )

        self.bulk_create_mgr.done()
        self.stdout.write("\n")
        self.stdout.write(f"Processed {total_existing}")

    @before_after_count(ContributorTeam)
    def handle_teams(self):
        # TODO(thenav56): Add typing?
        existing_teams = FH.ref("/v2/teams").get()
        current_teams_uuids = set(
            ContributorTeam.objects.values_list("old_id", flat=True),
        )
        total_existing = len(existing_teams)

        for i, (team_uuid, team_metadata) in enumerate(existing_teams.items(), start=1):  # type: ignore[reportAttributeAccessIssue]
            self.stdout.write(f"\rProcessing {i}/{total_existing}", ending="")
            if team_uuid in current_teams_uuids:
                continue

            logger.info("ContributorTeam - New: %s", team_metadata["teamName"])
            self.bulk_create_mgr.add(
                ContributorTeam(
                    client_id=str(ULID()),
                    old_id=team_uuid,
                    firebase_id=team_uuid,
                    name=team_metadata["teamName"],
                    created_by=self.bot_user,
                    modified_by=self.bot_user,
                    token=team_metadata["teamToken"],
                ),
            )
        self.stdout.write("\n")
        self.stdout.write(f"Processed {total_existing}")

        self.bulk_create_mgr.done()

    @before_after_count(ContributorUserGroup)
    def handle_contributor_user_groups(self):
        existing_cug_qs = existing_db_models.UserGroup.objects.all()

        current_cug_qs_uuid = set(
            ContributorUserGroup.objects.values_list("old_id", flat=True),
        )

        total_existing = existing_cug_qs.count()

        for i, existing_cug in enumerate(existing_cug_qs.all(), start=1):
            self.stdout.write(f"\rProcessing {i}/{total_existing}", ending="")

            if existing_cug.user_group_id in current_cug_qs_uuid:
                continue

            logger.info("Contributor User Group - New: %s", existing_cug.name)

            self.bulk_create_mgr.add(
                ContributorUserGroup(
                    client_id=str(ULID()),
                    old_id=existing_cug.user_group_id,
                    firebase_id=existing_cug.user_group_id,
                    name=existing_cug.name,
                    description=existing_cug.description.strip() if existing_cug.description else "",
                    created_at=parse_datetime(existing_cug.created_at),
                    archived_at=parse_datetime(existing_cug.archived_at, empty_fallback=None),
                    created_by_id=get_user_by_contributor_user_firebase_id(
                        existing_cug.created_by_id,
                        fallback=self.bot_user,
                    ),
                    modified_by_id=get_user_by_contributor_user_firebase_id(
                        existing_cug.created_by_id,
                        fallback=self.bot_user,
                    ),
                    archived_by_id=(
                        existing_cug.archived_by_id
                        and get_user_by_contributor_user_firebase_id(
                            existing_cug.archived_by_id,
                            fallback=self.bot_user,
                        )
                    ),
                    is_archived=existing_cug.is_archived,
                ),
            )

        self.bulk_create_mgr.done()
        self.stdout.write("\n")
        self.stdout.write(f"Processed {total_existing}")

    @before_after_count(ContributorUser)
    def handle_contributor_users(self):
        existing_qs = existing_db_models.User.objects.all()
        users_with_null_username = 0
        users_with_null_created_at = 0
        users_with_null_modified_at = 0

        # XXX(thenav56): Due to large number of users in db, we are using ignore_conflicts
        bulk_create_mgr = BulkCreateManager(chunk_size=1000, ignore_conflicts=True)

        total_existing = existing_qs.count()
        for i, existing_user in enumerate(existing_qs.iterator(), start=1):
            self.stdout.write(f"\rProcessing {i}/{total_existing}", ending="")
            self.stdout.flush()

            if existing_user.username is None:
                users_with_null_username += 1

            if existing_user.created is None:
                users_with_null_created_at += 1

            if existing_user.updated_at is None:
                users_with_null_modified_at += 1

            # TODO: Check if already exists? - This makes it very low
            # if ContributorUser.objects.filter(firebase_id=existing_user.user_id).exists():
            #     continue

            logger.info("ContributorUser - New/Update: %s", existing_user.username)

            bulk_create_mgr.add(
                ContributorUser(
                    firebase_id=existing_user.user_id,
                    username=existing_user.username or str(ULID()),
                    created_at=parse_datetime(existing_user.created),
                    modified_at=parse_datetime(existing_user.updated_at),
                    # TODO(thenav56): team=existing_user.team,
                ),
            )

        bulk_create_mgr.done()
        self.stdout.write("\n")

        for null_field, null_count in [
            ("username", users_with_null_username),
            ("created", users_with_null_created_at),
            ("updated_at", users_with_null_modified_at),
        ]:
            if null_count:
                self.stdout.write(
                    self.style.ERROR(
                        f"User with null {null_field}: {null_count}",
                    ),
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Bulk create summary: {bulk_create_mgr.summary()}",
            ),
        )

    @before_after_count(ContributorUserGroupMembership)
    def handle_contributor_user_user_group_memberships(self):
        existing_qs = existing_db_models.UserGroupUserMembership.objects.all()

        # XXX(thenav56): Due to large number of users in db, we are using ignore_conflicts
        bulk_create_mgr = BulkCreateManager(chunk_size=1000, ignore_conflicts=True)

        total_existing = existing_qs.count()

        for i, existing_membership in enumerate(existing_qs.iterator(), start=1):
            self.stdout.write(f"\rProcessing {i}/{total_existing}", ending="")
            self.stdout.flush()

            bulk_create_mgr.add(
                ContributorUserGroupMembership(
                    user_group_id=get_contributor_user_group_by_old_id(existing_membership.user_group_id),
                    user_id=get_contributor_user_id_by_firebase_id(existing_membership.user_id),
                    is_active=existing_membership.is_active,
                    # TODO(thenav56): team=existing_user.team,
                ),
            )

        bulk_create_mgr.done()
        self.stdout.write("\n")

        self.stdout.write(
            self.style.SUCCESS(
                f"Bulk create summary: {bulk_create_mgr.summary()}",
            ),
        )

    def _get_pre_parsed_project_names(self) -> dict[str, tuple[str, str, int, str]]:
        if self._pre_parsed_project_names:
            return self._pre_parsed_project_names

        self._pre_parsed_project_names = {}
        with Path.open(
            Config.BASE_DIR / "assets/migration/project-name-parsed.csv",
            mode="r",
            newline="",
            encoding="utf-8",
        ) as file:
            reader = csv.DictReader(file)
            for row in reader:
                self._pre_parsed_project_names[sanitize_name(row["name"])] = (
                    row["topic"],
                    row["region"],
                    int(row["number"]),
                    sanitize_name(row["requesting organization"]),
                )
        return self._pre_parsed_project_names

    @before_after_count([Project, ProjectAsset])
    def handle_project(self):
        existing_projects_qs = existing_db_models.Project.objects.all()

        # # TODO(thenav56): REMOVE THIS
        # Project.objects.filter(project_type=2).delete()

        total_existing = existing_projects_qs.count()
        for i, existing_project in enumerate(existing_projects_qs.iterator(chunk_size=10), start=1):
            self.stdout.write(f"\rProcessing {i}/{total_existing}", ending="")

            client_id = str(ULID())
            topic, region, project_number, requesting_organization = parse_project_name(
                self._get_pre_parsed_project_names(),
                existing_project.name,
            ) or (client_id, "N/A", 0, "")

            project, project_created = create_project(
                client_id=client_id,
                topic=topic,
                region=region,
                project_number=project_number,
                existing_project=existing_project,
                requesting_organization=requesting_organization,
                bot_user=self.bot_user,
            )

            if project_created:
                logger.info("Project - New %s/%s: %s", i, total_existing, project.generate_name())

            create_project_assets(project)

        self.stdout.write("\n")
        self.stdout.write(f"Processed {total_existing}")

    @before_after_count([AggregatedTracking, AggregatedUserStatData, AggregatedUserGroupStatData])
    def handle_aggregated_dataset(self):
        assert existing_db_models.AggregatedTracking.objects.count() == 2, "AggregatedTracking should always be two row"

        # XXX(thenav56): Due to large number of users in db, we are using ignore_conflicts
        bulk_create_mgr = BulkCreateManager(chunk_size=1000, ignore_conflicts=True)

        existing_user_qs = existing_db_models.AggregatedUserStatData.objects.all()
        total_existing_user = existing_user_qs.count()

        for i, existing_user_data in enumerate(existing_user_qs.iterator(), start=1):
            self.stdout.write(f"\rUserStat - Processing {i}/{total_existing_user}", ending="")
            self.stdout.flush()

            bulk_create_mgr.add(
                AggregatedUserStatData(
                    project_id=get_project_id_by_old_id(existing_user_data.project_id),
                    user_id=get_contributor_user_id_by_firebase_id(existing_user_data.user_id),
                    timestamp_date=existing_user_data.timestamp_date,
                    # Metric
                    total_time=existing_user_data.total_time,
                    task_count=existing_user_data.task_count,
                    swipes=existing_user_data.swipes,
                    area_swiped=existing_user_data.area_swiped,
                ),
            )
        self.stdout.write("\n")

        existing_user_group_qs = existing_db_models.AggregatedUserGroupStatData.objects.all()
        total_existing_user_group = existing_user_group_qs.count()

        for i, existing_user_group_data in enumerate(existing_user_group_qs.iterator(), start=1):
            self.stdout.write(f"\rUserGroupStat - Processing {i}/{total_existing_user_group}", ending="")
            self.stdout.flush()

            bulk_create_mgr.add(
                AggregatedUserGroupStatData(
                    project_id=get_project_id_by_old_id(existing_user_group_data.project_id),
                    user_id=get_contributor_user_id_by_firebase_id(existing_user_group_data.user_id),
                    user_group_id=get_contributor_user_group_id_by_old_id(existing_user_group_data.user_group_id),
                    timestamp_date=existing_user_group_data.timestamp_date,
                    # Metric
                    total_time=existing_user_group_data.total_time,
                    task_count=existing_user_group_data.task_count,
                    swipes=existing_user_group_data.swipes,
                    area_swiped=existing_user_group_data.area_swiped,
                ),
            )
        self.stdout.write("\n")

        bulk_create_mgr.done()

        # Update tracking data
        existing_user_tracking = existing_db_models.AggregatedTracking.objects.get(
            type=existing_db_models.AggregatedTracking.Type.AGGREGATED_USER_STAT_DATA_LATEST_DATE,
        )

        AggregatedTracking.objects.update_or_create(
            type=AggregatedTrackingTypeEnum.USER_DATA_LATEST_DATE,
            defaults={
                "updated_at": existing_user_tracking.updated_at,
                "value": existing_user_tracking.value,
            },
        )

        existing_user_group_tracking = existing_db_models.AggregatedTracking.objects.get(
            type=existing_db_models.AggregatedTracking.Type.AGGREGATED_USER_GROUP_STAT_DATA_LATEST_DATE,
        )

        AggregatedTracking.objects.update_or_create(
            type=AggregatedTrackingTypeEnum.USER_GROUP_DATA_LATEST_DATE,
            defaults={
                "updated_at": existing_user_group_tracking.updated_at,
                "value": existing_user_group_tracking.value,
            },
        )

    def handle_firebase(self):
        self.stdout.write("Fetching managers data from firebase authentication")

        # Load manager information from firebase
        user_qs = User.objects.filter(contributor_user__isnull=False).select_related("contributor_user")

        users_to_fetch_count = user_qs.count()

        for i, user in enumerate(user_qs.all(), start=1):
            user_firebase_id = user.contributor_user.firebase_id
            logger.info(
                "Fetching for user %s/%s: (pk=%s,firebase_id=%s)",
                i,
                users_to_fetch_count,
                user.pk,
                user_firebase_id,
            )

            user_fb_data = FH.auth.get_user(user_firebase_id)

            is_project_manager = user_fb_data.custom_claims.get("projectManager", False)
            is_disabled = user_fb_data.disabled
            is_active = True
            if not is_project_manager or is_disabled:
                is_active = False
                logger.warning(
                    "Setting user: %s as inactive because (is_project_manager=%s or is_disabled=%s)",
                    user.pk,
                    is_project_manager,
                    is_disabled,
                )

            user.email = user_fb_data.email
            user.is_active = is_active
            user.save(update_fields=("email", "is_active"))

    def _handle(self):
        self.handle_contributor_users()
        self.handle_organization()
        self.handle_teams()
        self.handle_contributor_user_groups()
        self.handle_contributor_user_user_group_memberships()
        # TODO(thenav56): We also need to migrate the area of interest as aoi input project asset
        # TODO: self.handle_contributor_user_user_group_memberships_logs()
        self.handle_project()
        self.handle_aggregated_dataset()
        self.handle_firebase()
        self.bulk_create_mgr.done()
        self.stdout.write(f"Bulk create summary: {self.bulk_create_mgr.summary()}")

    def setup_logger(self):
        # TODO(thenav56): This is not good enough... check again

        # Reset existing
        root_logger = logging.getLogger()

        # Create handlers
        log_destination_file = Config.BASE_DIR / "data-load-from-existing-system.log"

        self.stdout.write(self.style.SUCCESS(f"Streaming logging into {log_destination_file}"))

        file_handler = logging.FileHandler(log_destination_file)

        # Create formatters and add them to handlers
        formatter = logging.Formatter("%(asctime)s: - %(levelname)s - %(name)s - %(message)s")
        file_handler.setFormatter(formatter)

        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            root_logger.addHandler(file_handler)

        for name in logging.root.manager.loggerDict:
            logging.getLogger(name).handlers.clear()

        logger.setLevel(logging.INFO)

        # Add handlers to the logger
        logger.handlers.clear()
        logger.addHandler(file_handler)

        logger.info("Starting data migration")

    @typing.override
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "--timeout",
            "--timeout",
            type=int,
            default=600,
            help="The maximum time (in seconds) the command is allowed to run before timing out. Default is 10 min.",
        )
        parser.add_argument("--memray-enable", action="store_true", help="User memray to monitor memory usages")
        parser.add_argument("--memray-port", default="8888", type=int, help="specify a target port for memray live server")
        parser.add_argument(
            "--memray-host",
            default="0.0.0.0",  # noqa: S104 TODO(thenav56)
            type=str,
            help="specify a target host for memray live server",
        )
        # TODO(thenav56): Add argument to skip few steps... but we still need a dependency to avoid not found error if used

    @typing.override
    def handle(self, *args: typing.Any, **options: typing.Any):
        assert Config.EXISTING_SYSTEM_CONNECT_ENABLED is True, "Config EXISTING_SYSTEM_CONNECT_ENABLED is False"
        assert Config.ENABLE_DANGER_MODE is True, "ENABLE_DANGER_MODE needs to be enabled to use this command"

        self.setup_logger()

        memray = None

        with contextlib.suppress(ImportError):
            import memray  # type: ignore[reportMissingImports]

        memray_enable = options.get("memray_enable")

        if memray_enable:
            if memray is None:
                self.stdout.write(
                    self.style.ERROR("Make sure to install memray before using"),
                )
                return

            memray_host = options["memray_host"]
            memray_port = options["memray_port"]

            socket_dist = memray.SocketDestination(
                address=memray_host,
                server_port=memray_port,
            )
            self.stdout.write(
                self.style.WARNING(f"Running with memray live server, Exposed with: {memray_host}:{memray_port}"),
            )
            with memray.Tracker(destination=socket_dist):
                self._handle()
        else:
            self._handle()
