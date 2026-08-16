from django.contrib import admin

from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "display_order")
    list_filter = ("business",)
    search_fields = ("name", "business__name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "category", "price", "status")
    list_filter = ("status", "business", "category")
    search_fields = ("name", "business__name")
