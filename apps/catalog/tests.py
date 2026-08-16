from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.businesses.models import Business

from .models import Category, Product
from .services import (
    create_category,
    create_or_update_product,
    delete_category,
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
        self.assertEqual(product.status, Product.Status.INACTIVE)

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
