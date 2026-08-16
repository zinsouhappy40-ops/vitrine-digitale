from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from apps.core.images import process_uploaded_image

from .models import Category, Product


def get_dashboard_summary(business):
    products = Product.objects.for_business(business)
    categories = Category.objects.for_business(business)
    return {
        "product_count": products.count(),
        "active_product_count": products.filter(status=Product.Status.ACTIVE).count(),
        "category_count": categories.count(),
    }


def list_products(business):
    return Product.objects.for_business(business).select_related("category")


def list_categories(business):
    return Category.objects.for_business(business)


def create_category(*, business, name):
    category = Category(business=business, name=name.strip())
    category.full_clean()
    category.save()
    return category


def rename_category(category, *, name):
    category.name = name.strip()
    category.full_clean()
    category.save(update_fields=["name"])
    return category


@transaction.atomic
def delete_category(category):
    if category.name.casefold() == "divers":
        raise ValidationError("La catégorie Divers ne peut pas être supprimée.")

    business = category.business
    default_category = Category.objects.for_business(business).get(name="Divers")
    Product.objects.for_business(business).filter(category=category).update(
        category=default_category
    )
    category.delete()


@transaction.atomic
def create_or_update_product(*, business, cleaned_data, product=None):
    category = cleaned_data["category"]
    if category.business_id != business.id:
        raise ValidationError("La catégorie doit appartenir au même commerce.")
    if product is not None and product.business_id != business.id:
        raise ValidationError("Le produit doit appartenir au même commerce.")

    product = product or Product(business=business)
    old_image_name = product.image.name if product.pk and product.image else None
    for field in ("name", "price", "category", "description", "status"):
        setattr(product, field, cleaned_data[field])
    new_image = cleaned_data.get("image")
    if isinstance(new_image, UploadedFile):
        processed_image = process_uploaded_image(new_image)
        product.image.save(processed_image.name, processed_image, save=False)
    product.full_clean()
    product.save()
    if old_image_name and old_image_name != product.image.name:
        storage = product.image.storage
        transaction.on_commit(
            lambda storage=storage, name=old_image_name: storage.delete(name)
        )
    return product


def delete_product(product):
    product.delete()


def toggle_product_status(product):
    product.status = (
        Product.Status.INACTIVE
        if product.status == Product.Status.ACTIVE
        else Product.Status.ACTIVE
    )
    product.save(update_fields=["status", "updated_at"])
    return product
