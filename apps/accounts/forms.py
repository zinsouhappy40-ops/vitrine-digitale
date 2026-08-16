from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "autofocus": True,
                "placeholder": "vous@commerce.com",
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "placeholder": "Votre mot de passe",
            }
        ),
    )
    error_messages = {
        "invalid_login": "Adresse e-mail ou mot de passe incorrect.",
        "inactive": "Ce compte est désactivé.",
    }
