import logging
import typing

from celery import shared_task
from django.utils import timezone
from firebase_admin.db import Reference as FbReference
from pyfirebase_mapswipe import models as firebase_models
from pyfirebase_mapswipe import utils as firebase_utils

from apps.project.models import FirebasePushStatusEnum, Organization
from main.config import Config
from main.logging import log_extra

logger = logging.getLogger(__name__)


class InvalidOrganizationPushException(Exception): ...


def handle_new_organization_on_firebase(organization: Organization, organization_ref: FbReference):
    organization_data = firebase_models.FbOrganisation(
        name=organization.name,
        nameKey="",
        description=organization.description if organization.description else firebase_models.UNDEFINED,
        abbreviation=organization.abbreviation if organization.abbreviation else firebase_models.UNDEFINED,
        isArchived=organization.is_archived,
    )

    organization_ref.set(
        value={
            **firebase_utils.serialize(organization_data),
        },
    )


def handle_organization_update_on_firebase(organization: Organization, organization_ref: FbReference):
    organization_ref.update(
        value=firebase_utils.serialize(
            firebase_models.FbOrganisation(
                name=organization.name,
                nameKey="",
                description=organization.description if organization.description else firebase_models.UNDEFINED,
                abbreviation=organization.abbreviation if organization.abbreviation else firebase_models.UNDEFINED,
                isArchived=organization.is_archived,
            ),
        ),
    )


# FIXME(rup): use common push_django_to_firebase() method
@shared_task
def push_organization_to_firebase(organization_id: int):
    organization = Organization.objects.filter(id=organization_id).first()
    if not organization:
        return
    organization.update_firebase_push_status(FirebasePushStatusEnum.PROCESSING)

    try:
        organization_ref = Config.FIREBASE_HELPER.ref(
            Config.FirebaseKeys.organization(organization.id),
        )
        fb_organization: typing.Any = organization_ref.get()

        if not organization.firebase_last_pushed:
            if fb_organization is not None:
                logger.error(
                    "push_to_firebase found a organization already in firebase when creating a organization",
                    extra=log_extra({"organization": organization.pk}),
                )
                raise InvalidOrganizationPushException
            handle_new_organization_on_firebase(organization, organization_ref)
        else:
            if fb_organization is None:
                logger.error(
                    "push_to_firebase did not find organization in firebase when updating a organization",
                    extra=log_extra({"organization": organization.pk}),
                )
                raise InvalidOrganizationPushException
            handle_organization_update_on_firebase(organization, organization_ref)
    except InvalidOrganizationPushException:
        organization.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
    except Exception:
        logger.error(
            "push_to_firebase failed",
            extra=log_extra({"organization": organization.pk}),
            exc_info=True,
        )
        organization.update_firebase_push_status(FirebasePushStatusEnum.FAILED)
    else:
        organization.firebase_last_pushed = timezone.now()
        organization.update_firebase_push_status(FirebasePushStatusEnum.SUCCESS, commit=False)
        organization.save(
            update_fields=[
                "firebase_last_pushed",
                "firebase_push_status",
            ],
        )
