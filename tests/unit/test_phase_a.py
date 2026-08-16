from django.conf import settings
from django.db import connection
from django.test import SimpleTestCase, TestCase

from apps.accounts.models import User
from apps.businesses.models import Business
from apps.catalog.models import Category, Product


class PhaseAConfigurationTests(SimpleTestCase):
    def test_project_uses_postgresql_and_custom_user(self):
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.postgresql",
        )
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")

    def test_expected_models_are_registered(self):
        self.assertEqual(User._meta.label, "accounts.User")
        self.assertEqual(Business._meta.label, "businesses.Business")
        self.assertEqual(Category._meta.label, "catalog.Category")
        self.assertEqual(Product._meta.label, "catalog.Product")


class PhaseADatabaseTests(TestCase):
    def test_initial_schema_operates_on_postgresql(self):
        business = Business.objects.create(name="Boutique de test")
        owner = User.objects.create_user(
            email="owner@example.com",
            password="temporary-test-password",
            role=User.Role.BUSINESS_OWNER,
            business=business,
            is_staff=False,
        )
        category = Category.objects.create(
            business=business,
            name="Divers",
        )
        product = Product.objects.create(
            business=business,
            category=category,
            name="Produit de test",
            price="1000.00",
        )

        self.assertEqual(connection.vendor, "postgresql")
        self.assertEqual(owner.business, business)
        self.assertEqual(
            Product.objects.for_business(business).get(),
            product,
        )
