from django.urls import path

from . import views


app_name = "storefront"
urlpatterns = [
    path("<slug:slug>/", views.home, name="home"),
    path("<slug:slug>/catalogue/", views.catalogue, name="catalogue"),
    path(
        "<slug:slug>/produit/<int:pk>/",
        views.product_detail,
        name="product_detail",
    ),
    path("<slug:slug>/contact/", views.contact, name="contact"),
    path("<slug:slug>/qr/", views.qr, name="qr"),
]
