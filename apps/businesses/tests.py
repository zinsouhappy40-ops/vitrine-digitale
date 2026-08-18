from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from PIL import Image

from apps.catalog.models import Category

from .admin import BusinessAdminForm
from .models import Business
from .services import create_business_with_owner


User = get_user_model()


class BusinessServiceTests(TestCase):
    def test_slug_is_unique_when_names_collide(self):
        first = Business.objects.create(name="Marché Soleil")
        second = Business.objects.create(name="Marché Soleil")

        self.assertEqual(first.slug, "marche-soleil")
        self.assertEqual(second.slug, "marche-soleil-2")

    def test_create_business_with_owner_links_all_required_records(self):
        business, owner, temporary_password = create_business_with_owner(
            name="Boutique Service",
            owner_email="owner-service@example.com",
        )

        self.assertEqual(owner.business, business)
        self.assertEqual(owner.role, User.Role.BUSINESS_OWNER)
        self.assertFalse(owner.is_staff)
        self.assertTrue(owner.check_password(temporary_password))
        self.assertTrue(
            Category.objects.filter(business=business, name="Divers").exists()
        )

    def test_admin_form_validates_whatsapp_and_processes_logo(self):
        invalid_form = BusinessAdminForm(
            data={
                "name": "Boutique Admin",
                "description": "",
                "whatsapp_number": "+22997000000",
                "phone": "",
                "address": "",
                "opening_hours": "",
                "currency": "FCFA",
                "status": Business.Status.ACTIVE,
            },
        )

        self.assertFalse(invalid_form.is_valid())
        self.assertIn("whatsapp_number", invalid_form.errors)

        output = BytesIO()
        Image.new("RGBA", (1600, 800), color=(255, 0, 0, 128)).save(
            output,
            format="PNG",
        )
        upload = SimpleUploadedFile(
            "logo-original.png",
            output.getvalue(),
            content_type="image/png",
        )
        valid_data = invalid_form.data.copy()
        valid_data["whatsapp_number"] = "22997000000"
        form = BusinessAdminForm(data=valid_data, files={"logo": upload})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertRegex(form.cleaned_data["logo"].name, r"^[0-9a-f]{32}\.png$")
