from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from vendors.models import Vendor
from .models import (
    Category, Brand, Product, ProductReview,
    ProductQuestion, ProductAnswer
)


def home(request):
    """
    Home page view displaying featured categories, products, new arrivals, and top vendors.
    """
    # Get featured categories (root categories only)
    featured_categories = Category.objects.filter(parent__isnull=True, is_active=True)[:6]

    # Get featured products
    featured_products = Product.objects.filter(
        status='active',
        is_featured=True
    ).select_related('vendor').order_by('-created_at')[:8]

    # Get new products
    new_products = Product.objects.filter(
        status='active'
    ).select_related('vendor').order_by('-created_at')[:8]

    # Get top vendors based on review count and average rating
    top_vendors = Vendor.objects.filter(
        is_active=True,
        verification_status='verified'
    ).annotate(
        review_count=Count('reviews'),
        avg_rating=Avg('reviews__rating')
    ).filter(
        review_count__gt=0
    ).order_by('-avg_rating', '-review_count')[:4]

    context = {
        'featured_categories': featured_categories,
        'featured_products': featured_products,
        'new_products': new_products,
        'top_vendors': top_vendors,
    }

    return render(request, 'products/home.html', context)


def product_list(request):
    """
    View for displaying all products with filtering and sorting options.
    """
    # Get all active products
    products = Product.objects.filter(status='active')

    # Apply filters
    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    rating = request.GET.get('rating')
    sort = request.GET.get('sort', '-created_at')  # Default sorting by newest

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        # Include all child categories
        categories = [category] + list(category.get_all_children)
        products = products.filter(category__in=categories)

    if brand_slug:
        brand = get_object_or_404(Brand, slug=brand_slug)
        products = products.filter(brand=brand)

    if min_price:
        products = products.filter(current_price__gte=min_price)

    if max_price:
        products = products.filter(current_price__lte=max_price)

    if rating:
        products = products.annotate(avg_rating=Avg('reviews__rating')).filter(avg_rating__gte=rating)

    # Apply sorting
    if sort == 'price_asc':
        products = products.order_by('current_price')
    elif sort == 'price_desc':
        products = products.order_by('-current_price')
    elif sort == 'name_asc':
        products = products.order_by('title')
    elif sort == 'name_desc':
        products = products.order_by('-title')
    elif sort == 'rating':
        products = products.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    else:  # Default to newest
        products = products.order_by('-created_at')

    # Get all categories and brands for filtering
    categories = Category.objects.filter(parent__isnull=True, is_active=True)
    brands = Brand.objects.filter(is_active=True)

    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'brands': brands,
        'current_category': category_slug,
        'current_brand': brand_slug,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'current_rating': rating,
        'current_sort': sort,
    }

    return render(request, 'products/product_list.html', context)


def product_list_by_category(request, category_slug):
    """
    View for displaying products filtered by category.
    """
    category = get_object_or_404(Category, slug=category_slug)
    # Add the category filter to the request.GET dict and redirect to the main product list view
    url = f"{request.path}?category={category_slug}"
    return redirect(url)


def product_list_by_brand(request, brand_slug):
    """
    View for displaying products filtered by brand.
    """
    brand = get_object_or_404(Brand, slug=brand_slug)
    # Add the brand filter to the request.GET dict and redirect to the main product list view
    url = f"{request.path}?brand={brand_slug}"
    return redirect(url)


def product_detail(request, product_slug):
    """
    View for displaying product details.
    """
    product = get_object_or_404(Product, slug=product_slug, status='active')
    related_products = Product.objects.filter(
        category=product.category,
        status='active'
    ).exclude(id=product.id)[:4]

    # Get product reviews
    reviews = product.reviews.all().order_by('-created_at')

    # Get product questions
    questions = product.questions.all().prefetch_related('answers').order_by('-created_at')

    context = {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'questions': questions,
    }

    return render(request, 'products/product_detail.html', context)


def search_products(request):
    """
    View for searching products.
    """
    query = request.GET.get('q', '')

    if query:
        products = Product.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(meta_keywords__icontains=query) |
            Q(meta_description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query),
            status='active'
        ).distinct()
    else:
        products = Product.objects.none()

    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'query': query,
        'page_obj': page_obj,
    }

    return render(request, 'products/search_results.html', context)


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
