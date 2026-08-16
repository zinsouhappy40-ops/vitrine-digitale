from django import forms
from django.core.exceptions import ValidationError

from apps.core.images import validate_uploaded_image

from .models import Category, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name",)
        labels = {"name": "Nom"}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex. Vêtements"}),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip()


class ProductForm(forms.ModelForm):
    image = forms.FileField(
        label="Photo",
        required=False,
        widget=forms.FileInput(
            attrs={"accept": "image/jpeg,image/png,image/webp"}
        ),
    )

    class Meta:
        model = Product
        fields = (
            "name",
            "price",
            "category",
            "description",
            "image",
            "status",
        )
        labels = {
            "name": "Nom",
            "price": "Prix",
            "category": "Catégorie",
            "description": "Description",
            "status": "Statut",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nom du produit"}),
            "price": forms.NumberInput(attrs={"min": "0", "step": "0.01"}),
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Description courte (facultatif)"}
            ),
        }

    def __init__(self, *args, business, **kwargs):
        super().__init__(*args, **kwargs)
        self.business = business
        self.fields["category"].queryset = Category.objects.for_business(business)

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_description(self):
        return self.cleaned_data["description"].strip()

    def clean_category(self):
        category = self.cleaned_data["category"]
        if category.business_id != self.business.id:
            raise ValidationError("Cette catégorie n'appartient pas à votre commerce.")
        return category

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and hasattr(image, "size"):
            validate_uploaded_image(image)
        return image
