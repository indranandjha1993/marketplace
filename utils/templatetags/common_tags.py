from django import template
from django.db.models import Avg, Count, Q
from django.utils.safestring import mark_safe
from products.models import Product
from marketplace.models import CurrencySettings

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


@register.filter
def absolute(value):
    """Return the absolute value of a number."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value


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


@register.filter
def currency(value):
    """
    Format a number as currency according to the global currency settings.
    Usage: {{ product.price|currency }}
    """
    if value is None:
        return ''
    
    try:
        # Convert to float if it's not already
        value = float(value)
    except (ValueError, TypeError):
        return value
    
    # Get currency settings
    settings = CurrencySettings.get_currency_settings()
    
    # Format the number with the appropriate decimal and thousand separators
    formatted_number = '{:,.{prec}f}'.format(
        value, 
        prec=settings.decimal_places
    ).replace(',', 'X').replace('.', settings.decimal_separator).replace('X', settings.thousand_separator)
    
    # Add the currency symbol in the correct position
    if settings.symbol_position == 'before':
        return f'{settings.currency_symbol}{formatted_number}'
    else:
        return f'{formatted_number}{settings.currency_symbol}'


@register.simple_tag
def format_currency(value, show_symbol=True, decimal_places=None):
    """
    Advanced currency formatting with options.
    Usage: {% format_currency product.price [show_symbol=True] [decimal_places=None] %}
    """
    if value is None:
        return ''
    
    try:
        # Convert to float if it's not already
        value = float(value)
    except (ValueError, TypeError):
        return value
    
    # Get currency settings
    settings = CurrencySettings.get_currency_settings()
    
    # Use provided decimal places or default from settings
    places = decimal_places if decimal_places is not None else settings.decimal_places
    
    # Format the number with the appropriate decimal and thousand separators
    formatted_number = '{:,.{prec}f}'.format(
        value, 
        prec=places
    ).replace(',', 'X').replace('.', settings.decimal_separator).replace('X', settings.thousand_separator)
    
    # Add the currency symbol in the correct position if requested
    if not show_symbol:
        return formatted_number
    
    if settings.symbol_position == 'before':
        return f'{settings.currency_symbol}{formatted_number}'
    else:
        return f'{formatted_number}{settings.currency_symbol}'
