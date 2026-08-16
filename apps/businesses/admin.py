from django.contrib import admin, messages

from apps.accounts.models import User

from .forms import BusinessOwnerInlineForm
from .models import Business
from .services import ensure_default_category, update_business_status


class BusinessOwnerInline(admin.StackedInline):
    model = User
    form = BusinessOwnerInlineForm
    fields = ("email", "is_active")
    extra = 1
    min_num = 1
    max_num = 1
    validate_min = True
    validate_max = True
    can_delete = False
    verbose_name = "compte propriétaire"
    verbose_name_plural = "compte propriétaire"


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    readonly_fields = ("slug", "created_at")
    inlines = (BusinessOwnerInline,)
    actions = ("suspend_businesses", "reactivate_businesses")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            ensure_default_category(obj)

    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        for instance in instances:
            temporary_password = getattr(instance, "_temporary_password", None)
            if temporary_password:
                self.message_user(
                    request,
                    "Compte propriétaire créé. "
                    f"Mot de passe temporaire : {temporary_password}",
                    level=messages.WARNING,
                )

    @admin.action(description="Suspendre les commerces sélectionnés")
    def suspend_businesses(self, request, queryset):
        count = update_business_status(queryset, Business.Status.SUSPENDED)
        self.message_user(request, f"{count} commerce(s) suspendu(s).")

    @admin.action(description="Réactiver les commerces sélectionnés")
    def reactivate_businesses(self, request, queryset):
        count = update_business_status(queryset, Business.Status.ACTIVE)
        self.message_user(request, f"{count} commerce(s) réactivé(s).")


admin.site.site_header = "Vitrine Digitale"
admin.site.site_title = "Administration Vitrine Digitale"
admin.site.index_title = "Gestion des commerces"
