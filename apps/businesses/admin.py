from django import forms
from django.contrib import admin, messages
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from apps.accounts.models import User
from apps.core.images import process_uploaded_image, validate_uploaded_image

from .forms import BusinessOwnerInlineForm
from .models import Business
from .services import ensure_default_category, update_business_status


class BusinessAdminForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = "__all__"

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if isinstance(logo, UploadedFile):
            validate_uploaded_image(logo)
            return process_uploaded_image(logo, preserve_transparency=True)
        return logo


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
    form = BusinessAdminForm
    list_display = ("name", "slug", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    readonly_fields = ("slug", "created_at")
    inlines = (BusinessOwnerInline,)
    actions = ("suspend_businesses", "reactivate_businesses")

    def save_model(self, request, obj, form, change):
        old_logo_name = None
        if change and obj.pk:
            previous = Business.objects.only("logo").get(pk=obj.pk)
            old_logo_name = previous.logo.name if previous.logo else None

        super().save_model(request, obj, form, change)
        if old_logo_name and old_logo_name != obj.logo.name:
            storage = obj.logo.storage
            transaction.on_commit(
                lambda storage=storage, name=old_logo_name: storage.delete(name)
            )
        if not change:
            ensure_default_category(obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

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
