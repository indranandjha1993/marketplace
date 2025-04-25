from django import template
from django.db.models import Avg, Count, Q
from django.utils.safestring import mark_safe
from products.models import Product

register = template.Library()


@register.filter
def avg_rating(reviews):
    """Calculate the average rating from a QuerySet of reviews."""
    if reviews:
        result = reviews.aggregate(avg=Avg('rating'))
        if result['avg']:
            return round(result['avg'])
    return 0


@register.filter
def get_variant_attributes(variants):
    """Extract unique attributes from product variants."""
    attributes = set()
    for variant in variants:
        for attribute_value in variant.attribute_values.all():
            attributes.add(attribute_value.attribute)
    return list(attributes)


@register.filter
def has_variant_for_product(attribute_value, product):
    """Check if an attribute value is used in any variant of the given product."""
    return attribute_value.variants.filter(product=product).exists()


@register.simple_tag
def display_stars(rating, max_stars=5):
    """
    Displays star rating with FontAwesome icons.
    Usage: {% display_stars product.avg_rating %}
    """
    full_stars = min(int(rating), max_stars)
    empty_stars = max_stars - full_stars

    stars_html = []
    # Add filled stars
    for _ in range(full_stars):
        stars_html.append('<i class="fas fa-star text-warning"></i>')

    # Add empty stars
    for _ in range(empty_stars):
        stars_html.append('<i class="far fa-star text-warning"></i>')

    return mark_safe(''.join(stars_html))


@register.simple_tag
def rating_display(rating, review_count=None, max_stars=5):
    """
    Displays a complete rating with stars and review count.
    Usage: {% rating_display product.avg_rating product.reviews.count %}
    """
    stars = display_stars(rating, max_stars)

    if review_count is not None:
        count_text = f'<span class="text-muted ms-1">({review_count} review{"s" if review_count != 1 else ""})</span>'
    else:
        count_text = ''

    return mark_safe(f'<div class="product-rating">{stars}{count_text}</div>')


@register.filter
def get_item(dictionary, key):
    """Get a dictionary item by key safely."""
    if dictionary and key in dictionary:
        return dictionary[key]
    return None


@register.simple_tag
def total_category_products(category):
    """
    Count all products in a category including its subcategories.
    Usage: {% total_category_products category %}
    """
    # Get all subcategory IDs
    subcategory_ids = [category.id]
    
    # Add all children recursively
    children = category.get_all_children
    for child in children:
        subcategory_ids.append(child.id)
    
    # Count products in all these categories
    product_count = Product.objects.filter(
        category_id__in=subcategory_ids,
        status='active'
    ).count()
    
    return product_count
