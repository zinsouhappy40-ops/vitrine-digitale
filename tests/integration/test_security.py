from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from apps.businesses.models import Business


User = get_user_model()


class SecurityIntegrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.business = Business.objects.create(name="Boutique sécurité")
        self.owner = User.objects.create_user(
            email="security@example.com",
            password="valid-password",
            role=User.Role.BUSINESS_OWNER,
            business=self.business,
            is_staff=False,
        )

    def tearDown(self):
        cache.clear()

    def test_sixth_failed_login_is_temporarily_blocked(self):
        url = reverse("accounts:login")
        credentials = {
            "username": self.owner.email,
            "password": "wrong-password",
        }
        for _ in range(5):
            response = self.client.post(
                url,
                credentials,
                REMOTE_ADDR="198.51.100.20",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            credentials,
            REMOTE_ADDR="198.51.100.20",
        )

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Trop de tentatives", status_code=429)

    def test_email_rate_limit_cannot_be_bypassed_with_different_ips(self):
        url = reverse("accounts:login")
        credentials = {
            "username": self.owner.email.upper(),
            "password": "wrong-password",
        }
        for index in range(5):
            response = self.client.post(
                url,
                credentials,
                REMOTE_ADDR=f"198.51.100.{index + 1}",
            )
            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            credentials,
            REMOTE_ADDR="198.51.100.99",
        )

        self.assertEqual(response.status_code, 429)

    def test_login_and_dashboard_posts_require_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        login_response = csrf_client.post(
            reverse("accounts:login"),
            {"username": self.owner.email, "password": "valid-password"},
        )
        self.assertEqual(login_response.status_code, 403)

        csrf_client.force_login(self.owner)
        product_response = csrf_client.post(
            reverse("catalog:product_create"),
            {"name": "Produit sans jeton"},
        )
        self.assertEqual(product_response.status_code, 403)

    def test_security_headers_are_present(self):
        response = self.client.get(
            reverse("storefront:home", args=[self.business.slug])
        )

        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "same-origin")
