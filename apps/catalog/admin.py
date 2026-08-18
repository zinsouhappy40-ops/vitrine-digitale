from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from apps.core.images import process_uploaded_image, validate_uploaded_image

from .models import Category, Product
from .services import delete_category, delete_product


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if self.instance.pk:
            original_name = self.instance.name
            if original_name.casefold() == "divers" and name != original_name:
                raise ValidationError("La catégorie Divers ne peut pas être renommée.")
        return name


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if isinstance(image, UploadedFile):
            validate_uploaded_image(image)
            return process_uploaded_image(image)
        return image


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ("name", "business", "display_order")
    list_filter = ("business",)
    search_fields = ("name", "business__name")

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def has_delete_permission(self, request, obj=None):
        if obj and obj.name.casefold() == "divers":
            return False
        return super().has_delete_permission(request, obj)

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, _ = super().get_deleted_objects(
            objs, request
        )
        return deleted_objects, model_count, perms_needed, []

    def delete_model(self, request, obj):
        delete_category(obj)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ("name", "business", "category", "price", "status")
    list_filter = ("status", "business", "category")
    search_fields = ("name", "business__name")

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def save_model(self, request, obj, form, change):
        old_image_name = None
        if change and obj.pk:
            previous = (
                Product.objects.for_business(obj.business).only("image").get(pk=obj.pk)
            )
            old_image_name = previous.image.name if previous.image else None

        super().save_model(request, obj, form, change)
        if old_image_name and old_image_name != obj.image.name:
            storage = obj.image.storage
            transaction.on_commit(
                lambda storage=storage, name=old_image_name: storage.delete(name)
            )

    def delete_model(self, request, obj):
        delete_product(obj)
