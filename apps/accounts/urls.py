from django.urls import path

from .views import AccountLogoutView, EmailLoginView


app_name = "accounts"
urlpatterns = [
    path("connexion/", EmailLoginView.as_view(), name="login"),
    path("deconnexion/", AccountLogoutView.as_view(), name="logout"),
]
