from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.businesses.models import Business


def get_dashboard_business(user):
    if (
        not user.is_authenticated
        or user.role != User.Role.BUSINESS_OWNER
        or user.business_id is None
    ):
        raise PermissionDenied
    return user.business


def get_public_business(slug):
    return get_object_or_404(
        Business,
        slug=slug,
        status=Business.Status.ACTIVE,
    )
