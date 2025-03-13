from django import template
from django.db.models import Avg, Count

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
