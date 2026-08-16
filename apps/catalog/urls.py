from django.urls import path

from . import views


app_name = "catalog"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("produits/", views.product_list, name="product_list"),
    path("produits/nouveau/", views.product_create, name="product_create"),
    path(
        "produits/<int:pk>/modifier/",
        views.product_update,
        name="product_update",
    ),
    path(
        "produits/<int:pk>/supprimer/",
        views.product_delete,
        name="product_delete",
    ),
    path(
        "produits/<int:pk>/statut/",
        views.product_status,
        name="product_status",
    ),
    path("categories/", views.category_list, name="category_list"),
    path(
        "categories/nouveau/",
        views.category_create,
        name="category_create",
    ),
    path(
        "categories/<int:pk>/renommer/",
        views.category_rename,
        name="category_rename",
    ),
    path(
        "categories/<int:pk>/supprimer/",
        views.category_delete,
        name="category_delete",
    ),
]
