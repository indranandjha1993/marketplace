from django.db.models import Q, F, DecimalField, Avg, Case, When


def apply_product_filters(queryset, request):
    """
    Apply filters to product queryset based on request parameters.

    This centralizes all filtering logic for products to avoid duplication
    and ensure consistent filter behavior across the application.
    """
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        from products.models import Category
        try:
            category = Category.objects.get(slug=category_slug)
            # Include all child categories
            categories = [category]
            categories.extend(category.get_all_children)
            queryset = queryset.filter(category__in=categories)
        except Category.DoesNotExist:
            pass

    # Brand filter
    brand_slug = request.GET.get('brand')
    if brand_slug:
        queryset = queryset.filter(brand__slug=brand_slug)

    # Price filters - avoiding the 'current_price' property which is not a DB field
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Create a calculated field for the effective price (sale_price if not null, otherwise price)
    queryset = queryset.annotate(
        effective_price=Case(
            When(sale_price__isnull=False, then=F('sale_price')),
            default=F('price'),
            output_field=DecimalField()
        )
    )

    if min_price:
        try:
            min_price = float(min_price)
            queryset = queryset.filter(effective_price__gte=min_price)
        except (ValueError, TypeError):
            pass

    if max_price:
        try:
            max_price = float(max_price)
            queryset = queryset.filter(effective_price__lte=max_price)
        except (ValueError, TypeError):
            pass

    # Rating filter
    rating = request.GET.get('rating')
    if rating:
        try:
            rating = int(rating)
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=rating)
        except (ValueError, TypeError):
            pass

    # Search filter
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(meta_keywords__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        ).distinct()

    # Sorting
    sort = request.GET.get('sort', 'newest')

    if sort == 'price_asc':
        queryset = queryset.order_by('effective_price')
    elif sort == 'price_desc':
        queryset = queryset.order_by('-effective_price')
    elif sort == 'name_asc':
        queryset = queryset.order_by('title')
    elif sort == 'name_desc':
        queryset = queryset.order_by('-title')
    elif sort == 'rating':
        if not queryset.query.annotations.get('avg_rating'):
            queryset = queryset.annotate(avg_rating=Avg('reviews__rating'))
        queryset = queryset.order_by('-avg_rating')
    elif sort == 'relevance' and query:  # Only apply relevance sorting when there's a search query
        pass  # The default search behavior is already by relevance
    else:  # Default to newest
        queryset = queryset.order_by('-created_at')

    return queryset
