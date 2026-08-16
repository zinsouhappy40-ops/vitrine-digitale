from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from .managers import TenantScopedManager


def product_image_upload_to(instance, filename):
    extension = Path(filename).suffix.lower() or ".jpg"
    return f"products/{uuid4().hex}{extension}"


class Category(models.Model):
    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=80)
    display_order = models.PositiveIntegerField(default=0)

    objects = TenantScopedManager()

    class Meta:
        ordering = ["display_order", "name"]
        unique_together = (("business", "name"),)
        verbose_name = "catégorie"
        verbose_name_plural = "catégories"

    def __str__(self):
        return self.name


class Product(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Actif"
        INACTIVE = "inactive", "Inactif"

    business = models.ForeignKey(
        "businesses.Business",
        on_delete=models.CASCADE,
        related_name="products",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=80)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
    )
    description = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to=product_image_upload_to, null=True, blank=True)
    status = models.CharField(
        max_length=8,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        ordering = ["display_order", "name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name="catalog_product_price_non_negative",
            )
        ]
        verbose_name = "produit"
        verbose_name_plural = "produits"

    def clean(self):
        super().clean()
        if self.category_id and self.business_id:
            if self.category.business_id != self.business_id:
                raise ValidationError(
                    {"category": "La catégorie doit appartenir au même commerce."}
                )

    def __str__(self):
        return self.name
