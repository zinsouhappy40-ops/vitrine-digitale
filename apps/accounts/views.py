from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

from .forms import EmailAuthenticationForm


class EmailLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class AccountLogoutView(LogoutView):
    http_method_names = ["post", "options"]
    next_page = reverse_lazy("accounts:login")
