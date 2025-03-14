from django.db.models import Count
from products.models import Product, Category
from django.contrib.auth import get_user_model

User = get_user_model()


def get_recommendations_for_product(product, limit=4):
    """
    Returns product recommendations based on:
    1. Users who bought this also bought (collaborative)
    2. Products from same category (content-based)
    """
    # Start with products from same category and brand
    if product.brand:
        same_brand_category = Product.objects.filter(
            category=product.category,
            brand=product.brand,
            status='active'
        ).exclude(id=product.id)[:limit]

        if same_brand_category.count() >= limit:
            return same_brand_category

    # Products from same category
    same_category = Product.objects.filter(
        category=product.category,
        status='active'
    ).exclude(id=product.id)[:limit]

    if same_category.count() >= limit:
        return same_category

    # If we don't have enough recommendations yet, add products from the parent category
    if product.category.parent:
        parent_category_products = Product.objects.filter(
            category=product.category.parent,
            status='active'
        ).exclude(id=product.id)[:limit - same_category.count()]

        return list(same_category) + list(parent_category_products)

    # If still not enough, add popular products
    popular_products = Product.objects.filter(
        status='active'
    ).exclude(id=product.id).order_by('-view_count')[:limit]

    return popular_products


def get_personalized_recommendations(user, limit=4):
    """
    Get personalized recommendations based on user's purchase history
    """
    if not user.is_authenticated:
        # For anonymous users, return popular products
        return Product.objects.filter(status='active').order_by('-view_count')[:limit]

    # Get categories from user's purchase history
    from orders.models import OrderItem

    purchased_categories = Category.objects.filter(
        products__order_items__order__user=user
    ).annotate(purchase_count=Count('products__order_items')).order_by('-purchase_count')

    if purchased_categories.exists():
        # Get products from user's favorite categories
        favorite_category = purchased_categories.first()

        # Exclude products user has already purchased
        purchased_products = Product.objects.filter(
            order_items__order__user=user
        ).distinct()

        recommended_products = Product.objects.filter(
            category=favorite_category,
            status='active'
        ).exclude(id__in=purchased_products.values_list('id', flat=True))[:limit]

        if recommended_products.count() >= limit:
            return recommended_products

    # Fallback to popular products if no purchase history or not enough recommendations
    popular_products = Product.objects.filter(
        status='active'
    ).order_by('-view_count')[:limit]

    return popular_products
