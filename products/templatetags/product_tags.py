from django import template
from django.db.models import Avg

register = template.Library()


@register.filter
def avg_rating(reviews):
    """Calculate the average rating from a QuerySet of reviews."""
    if reviews:
        result = reviews.aggregate(avg=Avg('rating'))
        if result['avg']:
            return round(result['avg'])
    return 0
