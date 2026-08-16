from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import business_owner_required

from .forms import CategoryForm, ProductForm
from .models import Category, Product
from .services import (
    create_category,
    create_or_update_product,
    delete_category,
    delete_product,
    get_dashboard_summary,
    list_categories,
    list_products,
    rename_category,
    toggle_product_status,
)


@business_owner_required
def dashboard(request):
    business = request.user.business
    return render(
        request,
        "dashboard/index.html",
        {
            "business": business,
            "summary": get_dashboard_summary(business),
        },
    )


@business_owner_required
def product_list(request):
    return render(
        request,
        "dashboard/produits/list.html",
        {"products": list_products(request.user.business)},
    )


@business_owner_required
def product_create(request):
    business = request.user.business
    form = ProductForm(request.POST or None, request.FILES or None, business=business)
    if request.method == "POST" and form.is_valid():
        create_or_update_product(business=business, cleaned_data=form.cleaned_data)
        messages.success(request, "Produit ajouté.")
        return redirect("catalog:product_list")
    return render(request, "dashboard/produits/form.html", {"form": form})


@business_owner_required
def product_update(request, pk):
    business = request.user.business
    product = get_object_or_404(Product.objects.for_business(business), pk=pk)
    form = ProductForm(
        request.POST or None,
        request.FILES or None,
        instance=product,
        business=business,
    )
    if request.method == "POST" and form.is_valid():
        create_or_update_product(
            business=business,
            cleaned_data=form.cleaned_data,
            product=product,
        )
        messages.success(request, "Produit modifié.")
        return redirect("catalog:product_list")
    return render(
        request,
        "dashboard/produits/form.html",
        {"form": form, "product": product},
    )


@require_POST
@business_owner_required
def product_delete(request, pk):
    product = get_object_or_404(
        Product.objects.for_business(request.user.business),
        pk=pk,
    )
    delete_product(product)
    messages.success(request, "Produit supprimé.")
    return redirect("catalog:product_list")


@require_POST
@business_owner_required
def product_status(request, pk):
    product = get_object_or_404(
        Product.objects.for_business(request.user.business),
        pk=pk,
    )
    toggle_product_status(product)
    messages.success(request, "Statut du produit mis à jour.")
    return redirect("catalog:product_list")


@business_owner_required
def category_list(request):
    business = request.user.business
    form = CategoryForm()
    return render(
        request,
        "dashboard/categories/list.html",
        {"categories": list_categories(business), "form": form},
    )


@require_POST
@business_owner_required
def category_create(request):
    form = CategoryForm(request.POST)
    if form.is_valid():
        try:
            create_category(
                business=request.user.business,
                name=form.cleaned_data["name"],
            )
        except ValidationError as error:
            form.add_error("name", error)
        else:
            messages.success(request, "Catégorie ajoutée.")
            return redirect("catalog:category_list")
    return render(
        request,
        "dashboard/categories/list.html",
        {
            "categories": list_categories(request.user.business),
            "form": form,
        },
        status=400,
    )


@require_POST
@business_owner_required
def category_rename(request, pk):
    business = request.user.business
    category = get_object_or_404(Category.objects.for_business(business), pk=pk)
    form = CategoryForm(request.POST, instance=category)
    if form.is_valid():
        rename_category(category, name=form.cleaned_data["name"])
        messages.success(request, "Catégorie renommée.")
    else:
        messages.error(request, "Le nom de la catégorie est invalide.")
    return redirect("catalog:category_list")


@require_POST
@business_owner_required
def category_delete(request, pk):
    category = get_object_or_404(
        Category.objects.for_business(request.user.business),
        pk=pk,
    )
    try:
        delete_category(category)
    except ValidationError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, "Catégorie supprimée. Produits déplacés vers Divers.")
    return redirect("catalog:category_list")
