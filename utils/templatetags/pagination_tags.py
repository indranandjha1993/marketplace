from django import template

register = template.Library()


@register.inclusion_tag('includes/pagination.html')
def render_pagination(page_obj, request):
    """
    Renders a pagination component for the given page object.

    Usage: {% render_pagination page_obj request %}
    """
    return {
        'page_obj': page_obj,
        'request': request,
    }
