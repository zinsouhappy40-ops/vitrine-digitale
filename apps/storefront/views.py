from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.catalog.models import Category
from apps.core.tenant import get_public_business
from apps.core.qrcode import generate_qr_png

from .services import (
    get_active_products,
    build_page_meta,
    get_whatsapp_url,
    get_home_content,
    get_storefront_categories,
    group_catalog_products,
)


def home(request, slug):
    business = get_public_business(slug)
    categories, products = get_home_content(business)
    return render(
        request,
        "storefront/home.html",
        {
            "business": business,
            "categories": categories,
            "products": products,
            "meta": build_page_meta(request, business),
            "whatsapp_url": get_whatsapp_url(business),
        },
    )


def catalogue(request, slug):
    business = get_public_business(slug)
    categories = get_storefront_categories(business)
    selected_category = None
    category_id = request.GET.get("categorie")
    if category_id:
        selected_category = get_object_or_404(
            Category.objects.for_business(business),
            pk=category_id,
        )
    sections = group_catalog_products(business, selected_category)
    return render(
        request,
        "storefront/catalogue.html",
        {
            "business": business,
            "categories": categories,
            "selected_category": selected_category,
            "sections": sections,
            "meta": build_page_meta(request, business),
            "whatsapp_url": get_whatsapp_url(business),
        },
    )


def product_detail(request, slug, pk):
    business = get_public_business(slug)
    product = get_object_or_404(get_active_products(business), pk=pk)
    return render(
        request,
        "storefront/produit.html",
        {
            "business": business,
            "product": product,
            "meta": build_page_meta(request, business, product),
            "whatsapp_url": get_whatsapp_url(business, product),
        },
    )


def contact(request, slug):
    business = get_public_business(slug)
    return render(
        request,
        "storefront/contact.html",
        {
            "business": business,
            "meta": build_page_meta(request, business),
            "whatsapp_url": get_whatsapp_url(business),
        },
    )


def qr(request, slug):
    business = get_public_business(slug)
    storefront_url = request.build_absolute_uri(
        reverse("storefront:home", args=[business.slug])
    )
    return HttpResponse(generate_qr_png(storefront_url), content_type="image/png")
