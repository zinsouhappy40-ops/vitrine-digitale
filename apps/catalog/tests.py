from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from PIL import Image

from apps.businesses.models import Business

from .admin import ProductAdminForm
from .models import Category, Product
from .forms import ProductForm
from .services import (
    create_category,
    create_or_update_product,
    delete_category,
    get_recent_products,
    rename_category,
    toggle_product_status,
)


class CatalogServiceTests(TestCase):
    def setUp(self):
        self.business_a = Business.objects.create(name="Boutique A")
        self.business_b = Business.objects.create(name="Boutique B")
        self.default_a = Category.objects.create(
            business=self.business_a,
            name="Divers",
        )
        self.default_b = Category.objects.create(
            business=self.business_b,
            name="Divers",
        )

    def test_product_rejects_category_from_another_business(self):
        with self.assertRaises(ValidationError):
            create_or_update_product(
                business=self.business_a,
                cleaned_data={
                    "name": "Produit",
                    "price": Decimal("1000"),
                    "category": self.default_b,
                    "description": "",
                    "status": Product.Status.ACTIVE,
                },
            )

    def test_product_rejects_negative_price(self):
        with self.assertRaises(ValidationError):
            create_or_update_product(
                business=self.business_a,
                cleaned_data={
                    "name": "Produit",
                    "price": Decimal("-1"),
                    "category": self.default_a,
                    "description": "",
                    "status": Product.Status.ACTIVE,
                },
            )

    def test_toggle_product_status(self):
        product = Product.objects.create(
            business=self.business_a,
            category=self.default_a,
            name="Produit",
            price=1000,
        )
        toggle_product_status(product)
        product.refresh_from_db()
        self.assertEqual(product.status, Product.Status.INACTIVE)
        toggle_product_status(product)
        product.refresh_from_db()
        self.assertEqual(product.status, Product.Status.ACTIVE)

    def test_recent_products_are_tenant_scoped_and_limited(self):
        own_products = [
            Product.objects.create(
                business=self.business_a,
                category=self.default_a,
                name=f"Produit {index}",
                price=1000,
            )
            for index in range(6)
        ]
        Product.objects.create(
            business=self.business_b,
            category=self.default_b,
            name="Produit étranger",
            price=1000,
        )

        recent_products = list(get_recent_products(self.business_a))

        self.assertEqual(len(recent_products), 5)
        self.assertEqual(recent_products[0], own_products[-1])
        self.assertNotIn(own_products[0], recent_products)

    def test_default_category_cannot_be_renamed(self):
        with self.assertRaises(ValidationError):
            rename_category(self.default_a, name="Autre")

        self.default_a.refresh_from_db()
        self.assertEqual(self.default_a.name, "Divers")

    def test_category_delete_reassigns_products_to_default(self):
        category = Category.objects.create(
            business=self.business_a,
            name="Vêtements",
        )
        products = [
            Product.objects.create(
                business=self.business_a,
                category=category,
                name=f"Produit {index}",
                price=1000,
            )
            for index in range(3)
        ]

        delete_category(category)

        self.assertFalse(Category.objects.filter(pk=category.pk).exists())
        for product in products:
            product.refresh_from_db()
            self.assertEqual(product.category, self.default_a)

    def test_category_delete_recreates_missing_default(self):
        category = Category.objects.create(
            business=self.business_a,
            name="Vêtements",
        )
        Product.objects.create(
            business=self.business_a,
            category=category,
            name="Produit",
            price=1000,
        )
        self.default_a.delete()

        delete_category(category)

        self.assertTrue(
            Category.objects.filter(business=self.business_a, name="Divers").exists()
        )

    def test_category_name_is_unique_only_within_business(self):
        create_category(business=self.business_a, name="Accessoires")
        create_category(business=self.business_b, name="Accessoires")
        with self.assertRaises(ValidationError):
            create_category(business=self.business_a, name="Accessoires")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Category.objects.create(
                business=self.business_a,
                name="Accessoires",
            )


class ProductImageIntegrationTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.settings_override.enable()
        self.business = Business.objects.create(name="Boutique image")
        self.category = Category.objects.create(
            business=self.business,
            name="Divers",
        )

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_product_upload_is_resized_and_saved_with_uuid_name(self):
        output = BytesIO()
        Image.new("RGB", (1800, 900), color="blue").save(output, format="PNG")
        upload = SimpleUploadedFile(
            "original-product.png",
            output.getvalue(),
            content_type="image/png",
        )
        form = ProductForm(
            data={
                "name": "Produit illustré",
                "price": "2500",
                "category": self.category.pk,
                "description": "",
                "status": Product.Status.ACTIVE,
            },
            files={"image": upload},
            business=self.business,
        )
        self.assertTrue(form.is_valid(), form.errors)

        product = create_or_update_product(
            business=self.business,
            cleaned_data=form.cleaned_data,
        )

        self.assertRegex(product.image.name, r"^products/[0-9a-f]{32}\.jpg$")
        with product.image.open("rb") as stored_image:
            image = Image.open(stored_image)
            self.assertLessEqual(image.width, 1200)

    def test_product_admin_form_uses_image_pipeline(self):
        output = BytesIO()
        Image.new("RGB", (1800, 900), color="red").save(output, format="PNG")
        upload = SimpleUploadedFile(
            "admin-original.png",
            output.getvalue(),
            content_type="image/png",
        )
        form = ProductAdminForm(
            data={
                "business": self.business.pk,
                "category": self.category.pk,
                "name": "Produit admin",
                "price": "2500",
                "description": "",
                "status": Product.Status.ACTIVE,
                "display_order": 0,
            },
            files={"image": upload},
        )

        self.assertTrue(form.is_valid(), form.errors)
        processed_image = form.cleaned_data["image"]
        self.assertRegex(processed_image.name, r"^[0-9a-f]{32}\.jpg$")
        image = Image.open(processed_image)
        self.assertLessEqual(image.width, 1200)
