from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.SUPER_ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("business", None)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un super-admin doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un super-admin doit avoir is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super administrateur"
        BUSINESS_OWNER = "business_owner", "Propriétaire de commerce"

    username = None
    email = models.EmailField("adresse e-mail", unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    business = models.ForeignKey(
        "businesses.Business",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(role="super_admin", business__isnull=True, is_staff=True)
                    | Q(
                        role="business_owner",
                        business__isnull=False,
                        is_staff=False,
                    )
                ),
                name="accounts_user_role_business_staff_consistent",
            )
        ]

    def clean(self):
        super().clean()
        if self.role == self.Role.SUPER_ADMIN:
            if self.business_id is not None or not self.is_staff:
                raise ValidationError(
                    "Un super-admin doit être staff et sans commerce."
                )
        elif self.role == self.Role.BUSINESS_OWNER:
            if self.business_id is None or self.is_staff:
                raise ValidationError(
                    "Un propriétaire doit être lié à un commerce et non staff."
                )

    def __str__(self):
        return self.email
