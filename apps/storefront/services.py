from django.templatetags.static import static

from apps.catalog.models import Category, Product
from apps.core.whatsapp import build_whatsapp_url


def get_active_products(business):
    return (
        Product.objects.for_business(business)
        .filter(status=Product.Status.ACTIVE)
        .select_related("category", "business")
    )


def get_storefront_categories(business):
    return Category.objects.for_business(business)


def get_home_content(business):
    categories = list(get_storefront_categories(business))
    products = list(get_active_products(business)[:6])
    return categories, products


def group_catalog_products(business, selected_category=None):
    categories = list(get_storefront_categories(business))
    products = list(get_active_products(business))
    if selected_category is not None:
        categories = [selected_category]
        products = [
            product for product in products if product.category_id == selected_category.id
        ]

    products_by_category = {category.id: [] for category in categories}
    for product in products:
        if product.category_id in products_by_category:
            products_by_category[product.category_id].append(product)

    return [
        {"category": category, "products": products_by_category[category.id]}
        for category in categories
        if products_by_category[category.id]
    ]


def build_page_meta(request, business, product=None):
    if product is not None:
        title = f"{product.name} | {business.name}"
        description = product.description or (
            f"Découvrez {product.name} chez {business.name}."
        )
        image = product.image or business.logo
    else:
        title = f"{business.name} | Vitrine en ligne"
        description = business.description or (
            f"Découvrez les produits de {business.name}."
        )
        image = business.logo

    image_url = (
        request.build_absolute_uri(image.url)
        if image
        else request.build_absolute_uri(static("images/product-placeholder.svg"))
    )
    return {
        "title": title,
        "description": description[:200],
        "image_url": image_url,
        "url": request.build_absolute_uri(),
    }


def get_whatsapp_url(business, product=None):
    product_name = product.name if product else None
    return build_whatsapp_url(business.whatsapp_number, product_name)
