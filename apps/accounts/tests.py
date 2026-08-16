import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.businesses.models import Business
from apps.catalog.models import Category


User = get_user_model()


class AuthenticationFlowTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(name="Boutique A")
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="owner-password-123",
            role=User.Role.BUSINESS_OWNER,
            business=self.business,
            is_staff=False,
        )

    def test_owner_can_login_access_dashboard_and_logout(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.owner.email, "password": "owner-password-123"},
        )
        self.assertRedirects(response, reverse("catalog:dashboard"))

        response = self.client.get(reverse("catalog:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.business.name)

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        response = self.client.get(reverse("catalog:dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('catalog:dashboard')}",
        )

    def test_invalid_login_uses_generic_error(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "unknown@example.com", "password": "wrong-password"},
        )
        self.assertContains(response, "Adresse e-mail ou mot de passe incorrect.")

    def test_owner_cannot_access_django_admin(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("admin:index"))
        self.assertRedirects(
            response,
            f"{reverse('admin:login')}?next={reverse('admin:index')}",
        )


class AdministrationFlowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="admin-password-123",
        )
        self.client.force_login(self.admin)

    def test_super_admin_can_access_admin_but_not_owner_dashboard(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("catalog:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_business_admin_creates_owner_and_default_category(self):
        response = self.client.post(
            reverse("admin:businesses_business_add"),
            {
                "name": "Marché Soleil",
                "description": "",
                "whatsapp_number": "",
                "phone": "",
                "address": "",
                "opening_hours": "",
                "currency": "FCFA",
                "status": Business.Status.ACTIVE,
                "users-TOTAL_FORMS": "1",
                "users-INITIAL_FORMS": "0",
                "users-MIN_NUM_FORMS": "1",
                "users-MAX_NUM_FORMS": "1",
                "users-0-email": "soleil@example.com",
                "users-0-is_active": "on",
                "_save": "Enregistrer",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        business = Business.objects.get(name="Marché Soleil")
        owner = User.objects.get(email="soleil@example.com")
        self.assertEqual(owner.business, business)
        self.assertEqual(owner.role, User.Role.BUSINESS_OWNER)
        self.assertFalse(owner.is_staff)
        self.assertTrue(Category.objects.filter(business=business, name="Divers").exists())
        content = response.content.decode()
        match = re.search(r"Mot de passe temporaire : ([^<]+)", content)
        self.assertIsNotNone(match)
        self.assertTrue(owner.check_password(match.group(1).strip()))
