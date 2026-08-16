from pathlib import Path
from uuid import uuid4

from django.db import models
from django.utils.text import slugify


def business_logo_upload_to(instance, filename):
    extension = Path(filename).suffix.lower() or ".jpg"
    return f"businesses/logos/{uuid4().hex}{extension}"


class Business(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Actif"
        SUSPENDED = "suspended", "Suspendu"

    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=100, unique=True, editable=False)
    logo = models.ImageField(upload_to=business_logo_upload_to, null=True, blank=True)
    description = models.TextField(blank=True)
    whatsapp_number = models.CharField(max_length=15, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    opening_hours = models.CharField(max_length=255, blank=True)
    currency = models.CharField(max_length=10, default="FCFA")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "commerce"
        verbose_name_plural = "commerces"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "commerce"
            slug = base_slug
            suffix = 2
            while Business.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
