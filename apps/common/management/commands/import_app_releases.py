import json
import re
import sys
import typing
import urllib.request
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.common.firebase.push import FirebaseAppInfoPush
from apps.common.models import (
    APP_VERSION_VALIDATOR,
    AppInfo,
    AppPlatformEnum,
    AppRelease,
    get_app_version_code,
)

DEFAULT_SOURCE = "https://raw.githubusercontent.com/mapswipe/mapswipe-mobile/develop/changeLog.json"


def load_changelog(source: str) -> typing.Any:
    if source == "-":
        return json.load(sys.stdin)
    if source.startswith(("https://", "http://")):
        with urllib.request.urlopen(source, timeout=30) as response:  # noqa: S310
            return json.load(response)
    return json.loads(Path(source).read_text())


def changes_to_markdown(changes: list[str]) -> str:
    # NOTE: Some changes already start with a list marker. Eg: "* Fix login"
    items = (re.sub(r"^[-*•]\s+", "", change.strip()) for change in changes)
    return "\n".join(f"- {item}" for item in items if item)


class Command(BaseCommand):
    help = (
        "Import app releases from the mobile app's changeLog.json"
        ' ({"3.0.10": {"changes": ["..."]}}). Each version\'s changes become the release updates (markdown).'
    )

    @typing.override
    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "source",
            nargs="?",
            default=DEFAULT_SOURCE,
            help=f"Path, URL or - (stdin) of the changeLog.json. Defaults to {DEFAULT_SOURCE}",
        )
        parser.add_argument(
            "--platform",
            action="append",
            choices=[platform.label for platform in AppPlatformEnum],
            help="Platform to import into. Can be repeated. Defaults to all platforms.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Update the notes of releases that already exist. By default they are left as is.",
        )
        parser.add_argument(
            "--latest-version",
            help="Also set the latest version. Only releases up to this version are published.",
        )
        parser.add_argument(
            "--push",
            action="store_true",
            help="Push the app info to firebase after the import.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without saving anything.",
        )

    @typing.override
    def handle(self, *args, **options):  # type: ignore[reportMissingParameterType]
        changelog = load_changelog(options["source"])
        if not isinstance(changelog, dict):
            raise CommandError("Expected the changelog to be an object keyed by version")

        releases: dict[str, str] = {}
        for version, entry in changelog.items():
            try:
                APP_VERSION_VALIDATOR(version)
            except ValidationError:
                self.stderr.write(self.style.WARNING(f"Skipping invalid version: {version!r}"))
                continue
            releases[version] = changes_to_markdown((entry or {}).get("changes") or [])
        sorted_versions = sorted(releases, key=get_app_version_code)
        self.stdout.write(f"Found {len(sorted_versions)} versions: {', '.join(sorted_versions)}")

        latest_version: str | None = options["latest_version"]
        platforms = [AppPlatformEnum[label.upper()] for label in (options["platform"] or AppPlatformEnum.labels)]

        app_infos: list[AppInfo] = []
        with transaction.atomic():
            for platform in platforms:
                app_info = AppInfo.objects.filter(platform=platform).first()
                if app_info is None:
                    raise CommandError(f"App info for {platform.label} does not exist. Run the migrations first.")
                app_infos.append(app_info)

                existing_releases = {release.version: release for release in app_info.releases.all()}
                created, updated, skipped = [], [], []
                for version in sorted_versions:
                    updates = releases[version]
                    release = existing_releases.get(version)
                    if release is None:
                        AppRelease.objects.create(app_info=app_info, version=version, updates=updates)
                        created.append(version)
                    elif options["overwrite"] and release.updates != updates:
                        release.updates = updates
                        release.save(update_fields=["updates"])
                        updated.append(version)
                    else:
                        skipped.append(version)

                self.stdout.write(
                    f"[{platform.label}] created: {created or '-'}"
                    f" | updated: {updated or '-'}"
                    f" | unchanged: {skipped or '-'}",
                )

                if latest_version:
                    latest_release = app_info.releases.filter(version=latest_version).first()
                    if latest_release is None:
                        raise CommandError(f"[{platform.label}] Release {latest_version} does not exist")
                    app_info.latest_version = latest_release
                    try:
                        app_info.clean()
                    except ValidationError as e:
                        raise CommandError(f"[{platform.label}] {e}") from e
                    app_info.save(update_fields=["latest_version", "modified_at"])
                    self.stdout.write(f"[{platform.label}] latest version set to {latest_version}")

            if options["dry_run"]:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run: nothing was saved"))
                return

        if not options["push"]:
            self.stdout.write("Not pushed to firebase. Use --push or save the app info in the admin panel.")
            return

        for app_info in app_infos:
            FirebaseAppInfoPush(app_info).trigger(force_update=True)
            app_info.refresh_from_db()
            self.stdout.write(f"[{app_info.platform_enum.label}] firebase push: {app_info.firebase_push_status_enum}")
