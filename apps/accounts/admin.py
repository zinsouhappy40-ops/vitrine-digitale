from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.core.exceptions import ValidationError

from apps.businesses.services import reset_business_owner_password

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "role", "business", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("email", "business__name")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")
    actions = ("reset_temporary_password",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Compte", {"fields": ("role", "business", "is_active")}),
        ("Historique", {"fields": ("last_login", "date_joined")}),
    )

    def has_add_permission(self, request):
        return False

    @admin.action(description="Réinitialiser le mot de passe")
    def reset_temporary_password(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(
                request,
                "Sélectionnez un seul compte propriétaire.",
                level=messages.ERROR,
            )
            return

        user = queryset.first()
        try:
            temporary_password = reset_business_owner_password(user)
        except ValidationError as error:
            self.message_user(request, error.message, level=messages.ERROR)
            return
        self.message_user(
            request,
            f"Mot de passe temporaire pour {user.email} : {temporary_password}",
            level=messages.WARNING,
        )
