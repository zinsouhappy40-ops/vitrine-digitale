from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("", include("apps.accounts.urls")),
    path("dashboard/", include("apps.catalog.urls")),
    path("dashboard/", include("apps.businesses.urls")),
    path("admin/", admin.site.urls),
    path("", include("apps.storefront.urls")),
]

if settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            serve,
            {"document_root": settings.MEDIA_ROOT},
        )
    ]
