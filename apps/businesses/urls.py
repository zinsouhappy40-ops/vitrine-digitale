from django.urls import path

from . import views


app_name = "businesses"
urlpatterns = [
    path("commerce/", views.settings, name="settings"),
    path("mot-de-passe/", views.password_change, name="password_change"),
]
