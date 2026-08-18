from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.businesses.models import Business
from apps.catalog.models import Category, Product


User = get_user_model()


class DashboardTenantIsolationTests(TestCase):
    def setUp(self):
        self.business_a = Business.objects.create(name="Boutique A")
        self.business_b = Business.objects.create(name="Boutique B")
        self.owner_a = User.objects.create_user(
            email="a@example.com",
            password="password-a",
            role=User.Role.BUSINESS_OWNER,
            business=self.business_a,
            is_staff=False,
        )
        self.category_a = Category.objects.create(
            business=self.business_a,
            name="Vêtements",
        )
        self.category_b = Category.objects.create(
            business=self.business_b,
            name="Vêtements",
        )
        self.product_a = Product.objects.create(
            business=self.business_a,
            category=self.category_a,
            name="Chemise A",
            price=5000,
        )
        self.product_b = Product.objects.create(
            business=self.business_b,
            category=self.category_b,
            name="Pantalon secret B",
            price=7500,
        )
        self.client.force_login(self.owner_a)

    def test_product_list_contains_only_current_business(self):
        response = self.client.get(reverse("catalog:product_list"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["products"], [self.product_a])
        self.assertNotContains(response, self.product_b.name)

    def test_foreign_product_update_returns_404_without_data(self):
        response = self.client.get(
            reverse("catalog:product_update", args=[self.product_b.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotContains(response, self.product_b.name, status_code=404)

        post_response = self.client.post(
            reverse("catalog:product_update", args=[self.product_b.pk]),
            {
                "name": "Produit volé",
                "price": "1",
                "category": self.category_a.pk,
                "description": "Tentative",
                "status": Product.Status.ACTIVE,
            },
        )
        self.assertEqual(post_response.status_code, 404)
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_b.name, "Pantalon secret B")

    def test_foreign_product_delete_returns_404_and_preserves_product(self):
        response = self.client.post(
            reverse("catalog:product_delete", args=[self.product_b.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Product.objects.filter(pk=self.product_b.pk).exists())

    def test_foreign_category_rename_returns_404(self):
        response = self.client.post(
            reverse("catalog:category_rename", args=[self.category_b.pk]),
            {"name": "Catégorie volée"},
        )

        self.assertEqual(response.status_code, 404)
        self.category_b.refresh_from_db()
        self.assertEqual(self.category_b.name, "Vêtements")

    def test_foreign_product_status_returns_404(self):
        response = self.client.post(
            reverse("catalog:product_status", args=[self.product_b.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_b.status, Product.Status.ACTIVE)

    def test_foreign_category_delete_returns_404(self):
        response = self.client.post(
            reverse("catalog:category_delete", args=[self.category_b.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Category.objects.filter(pk=self.category_b.pk).exists())
