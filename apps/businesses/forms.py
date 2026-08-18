from django import forms
from django.contrib.auth.forms import PasswordChangeForm

from apps.accounts.models import User
from apps.core.images import validate_uploaded_image

from .models import Business
from .services import configure_business_owner


class BusinessOwnerInlineForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "is_active")

    def save(self, commit=True):
        user = super().save(commit=False)
        temporary_password = configure_business_owner(user)
        if temporary_password:
            user._temporary_password = temporary_password
        if commit:
            user.save()
        return user


class BusinessForm(forms.ModelForm):
    logo = forms.FileField(
        label="Logo",
        required=False,
        widget=forms.FileInput(
            attrs={"accept": "image/jpeg,image/png,image/webp"}
        ),
    )

    class Meta:
        model = Business
        fields = (
            "name",
            "logo",
            "description",
            "whatsapp_number",
            "phone",
            "address",
            "opening_hours",
        )
        labels = {
            "name": "Nom du commerce",
            "description": "Description",
            "whatsapp_number": "Numéro WhatsApp",
            "phone": "Téléphone",
            "address": "Adresse",
            "opening_hours": "Horaires",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "opening_hours": forms.TextInput(
                attrs={"placeholder": "Ex. Lun-Sam, 8h-19h"}
            ),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_whatsapp_number(self):
        return self.cleaned_data["whatsapp_number"].strip()

    def clean_phone(self):
        return self.cleaned_data["phone"].strip()

    def clean_address(self):
        return self.cleaned_data["address"].strip()

    def clean_opening_hours(self):
        return self.cleaned_data["opening_hours"].strip()

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if logo and hasattr(logo, "size"):
            validate_uploaded_image(logo)
        return logo


class OwnerPasswordChangeForm(PasswordChangeForm):
    pass
