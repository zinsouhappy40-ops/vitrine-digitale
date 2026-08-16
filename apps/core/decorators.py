from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from apps.accounts.models import User


def business_owner_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.role != User.Role.BUSINESS_OWNER or user.business_id is None:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped_view
