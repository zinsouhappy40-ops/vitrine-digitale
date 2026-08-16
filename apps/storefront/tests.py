from django.test import TestCase
from django.urls import reverse

from apps.businesses.models import Business
from apps.catalog.models import Category, Product


class StorefrontTests(TestCase):
    def setUp(self):
        self.business_a = Business.objects.create(
            name="Boutique A",
            description="La boutique A",
        )
        self.business_b = Business.objects.create(name="Boutique B")
        self.category_a = Category.objects.create(
            business=self.business_a,
            name="Vêtements",
        )
        self.category_b = Category.objects.create(
            business=self.business_b,
            name="Vêtements",
        )
        self.active_a = Product.objects.create(
            business=self.business_a,
            category=self.category_a,
            name="Chemise A",
            price=5000,
        )
        self.inactive_a = Product.objects.create(
            business=self.business_a,
            category=self.category_a,
            name="Produit inactif A",
            price=3000,
            status=Product.Status.INACTIVE,
        )
        self.active_b = Product.objects.create(
            business=self.business_b,
            category=self.category_b,
            name="Pantalon B secret",
            price=7500,
        )

    def test_home_displays_only_active_products_from_current_business(self):
        response = self.client.get(
            reverse("storefront:home", args=[self.business_a.slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.active_a.name)
        self.assertNotContains(response, self.inactive_a.name)
        self.assertNotContains(response, self.active_b.name)
        self.assertContains(response, "product-placeholder.svg")

    def test_catalogues_are_isolated_with_same_category_name(self):
        response_a = self.client.get(
            reverse("storefront:catalogue", args=[self.business_a.slug])
        )
        response_b = self.client.get(
            reverse("storefront:catalogue", args=[self.business_b.slug])
        )

        self.assertContains(response_a, self.active_a.name)
        self.assertNotContains(response_a, self.active_b.name)
        self.assertContains(response_b, self.active_b.name)
        self.assertNotContains(response_b, self.active_a.name)

    def test_foreign_or_inactive_product_returns_404(self):
        foreign_response = self.client.get(
            reverse(
                "storefront:product_detail",
                args=[self.business_a.slug, self.active_b.pk],
            )
        )
        inactive_response = self.client.get(
            reverse(
                "storefront:product_detail",
                args=[self.business_a.slug, self.inactive_a.pk],
            )
        )

        self.assertEqual(foreign_response.status_code, 404)
        self.assertEqual(inactive_response.status_code, 404)

    def test_unknown_or_suspended_business_returns_404(self):
        unknown_response = self.client.get(
            reverse("storefront:home", args=["commerce-inconnu"])
        )
        self.business_a.status = Business.Status.SUSPENDED
        self.business_a.save(update_fields=["status"])
        suspended_response = self.client.get(
            reverse("storefront:home", args=[self.business_a.slug])
        )

        self.assertEqual(unknown_response.status_code, 404)
        self.assertEqual(suspended_response.status_code, 404)
