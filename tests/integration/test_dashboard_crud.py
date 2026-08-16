from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.businesses.models import Business
from apps.catalog.models import Category, Product


User = get_user_model()


class DashboardCrudTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Boutique Test")
        self.owner = User.objects.create_user(
            email="owner-crud@example.com",
            password="owner-password",
            role=User.Role.BUSINESS_OWNER,
            business=self.business,
            is_staff=False,
        )
        self.default_category = Category.objects.create(
            business=self.business,
            name="Divers",
        )
        self.client.force_login(self.owner)

    def test_category_and_product_crud_flow(self):
        response = self.client.post(
            reverse("catalog:category_create"),
            {"name": "Vêtements"},
        )
        self.assertRedirects(response, reverse("catalog:category_list"))
        category = Category.objects.get(
            business=self.business,
            name="Vêtements",
        )

        response = self.client.post(
            reverse("catalog:product_create"),
            {
                "name": "Chemise",
                "price": "5000",
                "category": category.pk,
                "description": "Chemise légère",
                "status": Product.Status.ACTIVE,
            },
        )
        self.assertRedirects(response, reverse("catalog:product_list"))
        product = Product.objects.get(business=self.business, name="Chemise")

        response = self.client.post(
            reverse("catalog:product_update", args=[product.pk]),
            {
                "name": "Chemise premium",
                "price": "6000",
                "category": category.pk,
                "description": "Nouvelle description",
                "status": Product.Status.ACTIVE,
            },
        )
        self.assertRedirects(response, reverse("catalog:product_list"))
        product.refresh_from_db()
        self.assertEqual(product.name, "Chemise premium")

        response = self.client.post(
            reverse("catalog:product_status", args=[product.pk])
        )
        self.assertRedirects(response, reverse("catalog:product_list"))
        product.refresh_from_db()
        self.assertEqual(product.status, Product.Status.INACTIVE)

        response = self.client.post(
            reverse("catalog:product_delete", args=[product.pk])
        )
        self.assertRedirects(response, reverse("catalog:product_list"))
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_business_information_update_does_not_change_slug(self):
        original_slug = self.business.slug
        response = self.client.post(
            reverse("businesses:settings"),
            {
                "name": "Nouveau nom",
                "description": "Description",
                "whatsapp_number": "22997000000",
                "phone": "+229 01 00 00 00 00",
                "address": "Cotonou",
                "opening_hours": "Lun-Sam 8h-19h",
            },
        )

        self.assertRedirects(response, reverse("businesses:settings"))
        self.business.refresh_from_db()
        self.assertEqual(self.business.name, "Nouveau nom")
        self.assertEqual(self.business.slug, original_slug)
