from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.utils.crypto import get_random_string

from apps.accounts.models import User
from apps.catalog.models import Category
from apps.core.images import process_uploaded_image

from .models import Business


TEMPORARY_PASSWORD_CHARACTERS = (
    "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%"
)


def generate_temporary_password():
    return get_random_string(16, TEMPORARY_PASSWORD_CHARACTERS)


def ensure_default_category(business):
    category, _ = Category.objects.get_or_create(
        business=business,
        name="Divers",
        defaults={"display_order": 0},
    )
    return category


@transaction.atomic
def create_business_with_owner(*, name, owner_email):
    business = Business(name=name.strip())
    business.full_clean()
    business.save()
    ensure_default_category(business)

    temporary_password = generate_temporary_password()
    owner = User.objects.create_user(
        email=owner_email.strip(),
        password=temporary_password,
        role=User.Role.BUSINESS_OWNER,
        business=business,
        is_staff=False,
    )
    return business, owner, temporary_password


def configure_business_owner(user):
    user.role = User.Role.BUSINESS_OWNER
    user.is_staff = False
    user.is_superuser = False
    if user.pk:
        return None

    temporary_password = generate_temporary_password()
    user.set_password(temporary_password)
    return temporary_password


def reset_business_owner_password(user):
    if user.role != User.Role.BUSINESS_OWNER:
        raise ValidationError("Seul un compte propriétaire peut être réinitialisé.")
    temporary_password = generate_temporary_password()
    user.set_password(temporary_password)
    user.save(update_fields=["password"])
    return temporary_password


def update_business_status(queryset, status):
    if status not in Business.Status.values:
        raise ValueError("Statut de commerce invalide.")
    return queryset.update(status=status)


@transaction.atomic
def update_business_information(business, cleaned_data):
    fields = (
        "name",
        "description",
        "whatsapp_number",
        "phone",
        "address",
        "opening_hours",
    )
    for field in fields:
        setattr(business, field, cleaned_data[field])
    old_logo_name = business.logo.name if business.logo else None
    new_logo = cleaned_data.get("logo")
    if isinstance(new_logo, UploadedFile):
        processed_logo = process_uploaded_image(
            new_logo,
            preserve_transparency=True,
        )
        business.logo.save(processed_logo.name, processed_logo, save=False)
    business.full_clean()
    update_fields = [*fields]
    if isinstance(new_logo, UploadedFile):
        update_fields.append("logo")
    business.save(update_fields=update_fields)
    if old_logo_name and old_logo_name != business.logo.name:
        storage = business.logo.storage
        transaction.on_commit(
            lambda storage=storage, name=old_logo_name: storage.delete(name)
        )
    return business
