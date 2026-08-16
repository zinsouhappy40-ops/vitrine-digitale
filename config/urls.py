from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("apps.accounts.urls")),
    path("dashboard/", include("apps.catalog.urls")),
    path("dashboard/", include("apps.businesses.urls")),
    path("admin/", admin.site.urls),
    path("", include("apps.storefront.urls")),
]
