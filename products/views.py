import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from marketplace.models import CurrencySettings
from utils.product_recommendations import get_recommendations_for_product, get_personalized_recommendations
from vendors.models import Vendor
from .models import (
    Category, Brand, Product, ProductReview,
    ProductQuestion, ProductAnswer, ProductVariant
)
from .utils.product_filters import apply_product_filters


def home(request):
    """
    Home page view displaying featured categories, products, new arrivals, and top vendors.
    """
    # Get featured categories (root categories only)
    featured_categories = Category.objects.filter(parent__isnull=True, is_active=True)[:6]

    # Get featured products - with effective_price annotation
    featured_products = Product.objects.filter(
        status='active',
        is_featured=True
    ).select_related('vendor')

    # Annotate with effective_price for sorting
    featured_products = Product.annotate_current_price(featured_products).order_by('-created_at')[:8]

    # Get new products
    new_products = Product.objects.filter(
        status='active'
    ).select_related('vendor')

    # Annotate with effective_price for sorting
    new_products = Product.annotate_current_price(new_products).order_by('-created_at')[:8]

    # Get top vendors based on review count and average rating
    top_vendors = Vendor.objects.filter(
        is_active=True,
        verification_status='verified'
    ).annotate(
        review_count=Count('reviews'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-avg_rating', '-review_count')[:4]

    context = {
        'featured_categories': featured_categories,
        'featured_products': featured_products,
        'new_products': new_products,
        'top_vendors': top_vendors,
    }

    return render(request, 'products/home.html', context)

def product_detail(request, product_slug):
    """
    View for displaying a single product with details, reviews, and questions.
    :param request:
    :param product_slug:
    :return:
    """
    product = get_object_or_404(
        Product.objects.select_related('vendor', 'brand', 'category')
        .prefetch_related('variants__attribute_values__attribute', 'images', 'reviews', 'questions__answers'),
        slug=product_slug, status='active'
    )

    Product.objects.filter(id=product.id).update(view_count=F('view_count') + 1)

    variants_data = []
    default_attributes = {}
    if product.variants.exists():
        default_variant = product.variants.filter(quantity__gt=0, is_active=True).first()
        if default_variant:
            default_attributes = {attr_value.attribute.name: attr_value.id for attr_value in
                                  default_variant.attribute_values.all()}
        for variant in product.variants.filter(is_active=True).all():
            variant_data = {
                'id': variant.id,
                'price': float(variant.price),
                'sale_price': float(variant.current_price),
                'quantity': variant.quantity,
                'sku': variant.sku,
                'attributes': {attr_value.attribute.name: attr_value.id for attr_value in
                               variant.attribute_values.all()},
                'discount_percentage': variant.discount_percentage if variant.is_on_sale else 0,
                'is_in_stock': variant.is_in_stock,
                'is_on_sale': variant.is_on_sale,
            }
            variants_data.append(variant_data)

    variants_json = json.dumps(variants_data)

    related_products = get_recommendations_for_product(product)
    personalized_recommendations = get_personalized_recommendations(request.user)
    reviews = product.reviews.all().order_by('-created_at')
    questions = product.questions.all().prefetch_related('answers').order_by('-created_at')

    meta_description = product.meta_description or product.description[:160]
    meta_keywords = product.meta_keywords or f"{product.title}, {product.category.name}, {product.brand.name if product.brand else ''}"

    all_variants_out_of_stock = product.variants.exists() and not product.variants.filter(quantity__gt=0).exists()
    
    # Get currency settings for JavaScript
    currency_settings = CurrencySettings.get_currency_settings()

    context = {
        'product': product,
        'related_products': related_products,
        'personalized_recommendations': personalized_recommendations,
        'reviews': reviews,
        'questions': questions,
        'variants_json': variants_json,
        'default_attributes': default_attributes,
        'all_variants_out_of_stock': all_variants_out_of_stock,
        'meta_title': f"{product.title} | {product.brand.name if product.brand else ''} | Marketplace",
        'meta_description': meta_description,
        'meta_keywords': meta_keywords,
        'og_image': product.primary_image.image.url if product.primary_image else None,
        'currency_settings': currency_settings,
    }

    return render(request, 'products/product_detail.html', context)

def product_list_by_category(request, category_slug):
    """
    View for displaying products filtered by category.
    """
    return redirect(f"{reverse('products:browse_products')}?category={category_slug}")


def product_list_by_brand(request, brand_slug):
    """
    View for displaying products filtered by brand.
    """
    return redirect(f"{reverse('products:browse_products')}?brand={brand_slug}")


def browse_products(request):
    """
    View for browsing and searching products with filtering and sorting options.
    """
    # Start with all active products
    products = Product.objects.filter(status='active').select_related('vendor', 'category', 'brand')

    # Track if there's a search query
    search_query = request.GET.get('q', '')

    # Apply filters from centralized utility - this already handles search
    products = apply_product_filters(products, request)

    # If there's no search query and no filters, show all products (browse mode)
    # If there's a search query but no results, show empty results (search mode)
    is_search_mode = bool(search_query)

    # Determine if there are any active filters beyond sorting
    has_active_filters = any([
        request.GET.get('q'),
        request.GET.get('category'),
        request.GET.get('brand'),
        request.GET.get('min_price'),
        request.GET.get('max_price'),
        request.GET.get('rating'),
        request.GET.get('sort') and request.GET.get('sort') not in ['newest', 'relevance']
    ])

    # Get all categories and brands for filtering sidebar
    categories = Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related('children')
    brands = Brand.objects.filter(is_active=True)

    # Get current category and brand objects for breadcrumbs
    current_category_obj = None
    current_brand_obj = None
    breadcrumb_categories = []

    if request.GET.get('category'):
        try:
            current_category_obj = Category.objects.get(slug=request.GET.get('category'))

            # Build breadcrumb path
            category = current_category_obj
            while category:
                breadcrumb_categories.insert(0, category)
                category = category.parent
        except Category.DoesNotExist:
            pass

    if request.GET.get('brand'):
        try:
            current_brand_obj = Brand.objects.get(slug=request.GET.get('brand'))
        except Brand.DoesNotExist:
            pass

    # Pagination
    paginator = Paginator(products, 18)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Determine default sort based on mode
    default_sort = 'relevance' if is_search_mode else 'newest'
    current_sort = request.GET.get('sort', default_sort)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'brands': brands,
        'query': search_query,
        'is_search_mode': is_search_mode,
        'current_category': request.GET.get('category'),
        'current_brand': request.GET.get('brand'),
        'current_min_price': request.GET.get('min_price'),
        'current_max_price': request.GET.get('max_price'),
        'current_rating': request.GET.get('rating'),
        'current_sort': current_sort,
        'current_category_obj': current_category_obj,
        'current_brand_obj': current_brand_obj,
        'breadcrumb_categories': breadcrumb_categories,
        'has_active_filters': has_active_filters,
    }

    return render(request, 'products/product_browse.html', context)

@login_required
@require_POST
def add_review(request, product_slug):
    """
    View for adding a product review.
    """
    product = get_object_or_404(Product, slug=product_slug)

    # Check if user has already reviewed this product
    if ProductReview.objects.filter(product=product, user=request.user).exists():
        messages.error(request, 'You have already reviewed this product')
        return redirect('products:product_detail', product_slug=product_slug)

    rating = request.POST.get('rating')
    title = request.POST.get('title')
    comment = request.POST.get('comment')

    if not rating:
        messages.error(request, 'Please provide a rating')
        return redirect('products:product_detail', product_slug=product_slug)

    # Create the review
    review = ProductReview.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        title=title,
        comment=comment,
        # Check if the user has purchased this product
        is_verified_purchase=product.order_items.filter(order__user=request.user).exists()
    )

    messages.success(request, 'Review added successfully')
    return redirect('products:product_detail', product_slug=product_slug)


@login_required
@require_POST
def ask_question(request, product_slug):
    """
    View for asking a product question.
    """
    product = get_object_or_404(Product, slug=product_slug)
    question = request.POST.get('question')

    if not question:
        messages.error(request, 'Please enter a question')
        return redirect('products:product_detail', product_slug=product_slug)

    # Create the question
    ProductQuestion.objects.create(
        product=product,
        user=request.user,
        question=question
    )

    messages.success(request, 'Your question has been submitted')
    return redirect('products:product_detail', product_slug=product_slug)


@login_required
@require_POST
def answer_question(request, question_id):
    """
    View for answering a product question.
    """
    question = get_object_or_404(ProductQuestion, id=question_id)
    answer = request.POST.get('answer')

    if not answer:
        messages.error(request, 'Please enter an answer')
        return redirect('products:product_detail', product_slug=question.product.slug)

    # Check if the user is the vendor of this product
    is_vendor = request.user.is_vendor and hasattr(request.user,
                                                   'vendor') and request.user.vendor == question.product.vendor

    # Create the answer
    ProductAnswer.objects.create(
        question=question,
        user=request.user,
        answer=answer,
        is_vendor=is_vendor
    )

    messages.success(request, 'Your answer has been submitted')
    return redirect('products:product_detail', product_slug=question.product.slug)


def check_variant_quantity(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    return JsonResponse({'quantity': variant.quantity})
