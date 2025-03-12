from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.shortcuts import render, redirect, get_object_or_404

from products.models import Product
from .models import Vendor


def vendor_list(request):
    """
    View for displaying all verified vendors.
    """
    vendors = Vendor.objects.filter(
        is_active=True,
        verification_status='verified'
    ).annotate(
        product_count=Count('products'),
        avg_rating=Avg('reviews__rating')
    ).order_by('-joined_date')

    # Pagination
    paginator = Paginator(vendors, 16)  # 16 vendors per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'vendor_count': vendors.count(),
    }

    return render(request, 'vendors/vendor_list.html', context)


def vendor_detail(request, vendor_slug):
    """
    View for displaying vendor details and their products.
    """
    vendor = get_object_or_404(
        Vendor.objects.annotate(
            product_count=Count('products'),
            avg_rating=Avg('reviews__rating')
        ),
        slug=vendor_slug,
        is_active=True
    )

    # Get vendor's products
    products = Product.objects.filter(
        vendor=vendor,
        status='active'
    )

    # Apply filters and sorting
    category_id = request.GET.get('category')
    sort = request.GET.get('sort', '-created_at')  # Default sorting by newest

    if category_id:
        products = products.filter(category_id=category_id)

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

    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get vendor reviews
    reviews = vendor.reviews.all().order_by('-created_at')

    context = {
        'vendor': vendor,
        'page_obj': page_obj,
        'product_count': products.count(),
        'reviews': reviews,
        'current_category': category_id,
        'current_sort': sort,
    }

    return render(request, 'vendors/vendor_detail.html', context)


@login_required
def become_vendor(request):
    """
    View for registering as a vendor.
    """
    # Check if the user is already a vendor
    if hasattr(request.user, 'vendor'):
        messages.info(request, 'You are already registered as a vendor')
        return redirect('vendors:vendor_dashboard')

    if request.method == 'POST':
        # Process form data
        business_name = request.POST.get('business_name')
        description = request.POST.get('description')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        postal_code = request.POST.get('postal_code')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        website = request.POST.get('website')
        tax_id = request.POST.get('tax_id')

        # Validate form data
        if not all([business_name, description, address, city, state, country, postal_code, phone_number, email]):
            messages.error(request, 'Please fill in all required fields')
            return render(request, 'vendors/become_vendor.html')

        # Create vendor profile
        vendor = Vendor.objects.create(
            user=request.user,
            business_name=business_name,
            description=description,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            phone_number=phone_number,
            email=email,
            website=website,
            tax_id=tax_id,
            verification_status='pending'
        )

        # Handle document uploads
        if 'identity_doc' in request.FILES:
            vendor.documents.create(
                document_type='identity',
                document=request.FILES['identity_doc']
            )

        if 'address_doc' in request.FILES:
            vendor.documents.create(
                document_type='address',
                document=request.FILES['address_doc']
            )

        if 'business_doc' in request.FILES:
            vendor.documents.create(
                document_type='business',
                document=request.FILES['business_doc']
            )

        messages.success(request,
                         'Your vendor application has been submitted successfully. We will review your application and get back to you soon.')
        return redirect('products:home')

    return render(request, 'vendors/become_vendor.html')


@login_required
def vendor_dashboard(request):
    """
    Main vendor dashboard.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    # Get recent orders
    recent_orders = vendor.orders.all().order_by('-created_at')[:5]

    # Get sales statistics
    total_sales = sum(
        order.total_vendor_amount for order in vendor.orders.filter(status__in=['processing', 'shipped', 'delivered']))
    total_orders = vendor.orders.count()
    pending_orders = vendor.orders.filter(status='pending').count()

    # Get product statistics
    total_products = vendor.products.count()
    active_products = vendor.products.filter(status='active').count()
    out_of_stock = vendor.products.filter(status='active', quantity=0).count()

    context = {
        'vendor': vendor,
        'recent_orders': recent_orders,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_products': total_products,
        'active_products': active_products,
        'out_of_stock': out_of_stock,
    }

    return render(request, 'vendors/dashboard/index.html', context)


@login_required
def vendor_products(request):
    """
    Vendor product management.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    # Get all vendor products
    products = vendor.products.all().order_by('-created_at')

    # Filter by status if requested
    status = request.GET.get('status')
    if status:
        products = products.filter(status=status)

    # Search by name if requested
    search = request.GET.get('search')
    if search:
        products = products.filter(title__icontains=search)

    # Pagination
    paginator = Paginator(products, 10)  # 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vendor': vendor,
        'page_obj': page_obj,
        'current_status': status,
        'search_query': search,
    }

    return render(request, 'vendors/dashboard/products.html', context)


@login_required
def add_product(request):
    """
    Add a new product as a vendor.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    # Handle form submission
    if request.method == 'POST':
        # Process product form
        # This would be a more complex form handling with image uploads, variants, etc.
        # For now, just a placeholder
        messages.success(request, 'Product added successfully')
        return redirect('vendors:vendor_products')

    context = {
        'vendor': vendor,
    }

    return render(request, 'vendors/dashboard/add_product.html', context)


@login_required
def edit_product(request, product_slug):
    """
    Edit an existing product as a vendor.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    # Get the product
    product = get_object_or_404(Product, slug=product_slug, vendor=vendor)

    # Handle form submission
    if request.method == 'POST':
        # Process product form
        # This would be a more complex form handling with image uploads, variants, etc.
        # For now, just a placeholder
        messages.success(request, 'Product updated successfully')
        return redirect('vendors:vendor_products')

    context = {
        'vendor': vendor,
        'product': product,
    }

    return render(request, 'vendors/dashboard/edit_product.html', context)


@login_required
def vendor_orders(request):
    """
    View for managing vendor orders.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    # Get all vendor orders
    orders = vendor.orders.all().order_by('-created_at')

    # Filter by status if requested
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    # Search by order number if requested
    search = request.GET.get('search')
    if search:
        orders = orders.filter(order__order_number__icontains=search)

    # Pagination
    paginator = Paginator(orders, 10)  # 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vendor': vendor,
        'page_obj': page_obj,
        'current_status': status,
        'search_query': search,
    }

    return render(request, 'vendors/dashboard/orders.html', context)


@login_required
def vendor_order_detail(request, order_number):
    """
    View for viewing and managing a specific vendor order.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    # Get the order
    vendor_order = get_object_or_404(vendor.orders, order__order_number=order_number)

    # Get order items for this vendor
    order_items = vendor_order.order.items.filter(product__vendor=vendor)

    context = {
        'vendor': vendor,
        'vendor_order': vendor_order,
        'order_items': order_items,
    }

    return render(request, 'vendors/dashboard/order_detail.html', context)


@login_required
def vendor_profile(request):
    """
    View for editing vendor profile.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    # Handle form submission
    if request.method == 'POST':
        # Update vendor profile
        vendor.business_name = request.POST.get('business_name', vendor.business_name)
        vendor.description = request.POST.get('description', vendor.description)
        vendor.address = request.POST.get('address', vendor.address)
        vendor.city = request.POST.get('city', vendor.city)
        vendor.state = request.POST.get('state', vendor.state)
        vendor.country = request.POST.get('country', vendor.country)
        vendor.postal_code = request.POST.get('postal_code', vendor.postal_code)
        vendor.phone_number = request.POST.get('phone_number', vendor.phone_number)
        vendor.email = request.POST.get('email', vendor.email)
        vendor.website = request.POST.get('website', vendor.website)

        # Handle logo and banner uploads
        if 'logo' in request.FILES:
            vendor.logo = request.FILES['logo']

        if 'banner' in request.FILES:
            vendor.banner = request.FILES['banner']

        vendor.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('vendors:vendor_profile')

    context = {
        'vendor': vendor,
    }

    return render(request, 'vendors/dashboard/profile.html', context)


@login_required
def vendor_settings(request):
    """
    View for vendor account settings.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    context = {
        'vendor': vendor,
    }

    return render(request, 'vendors/dashboard/settings.html', context)


@login_required
def vendor_analytics(request):
    """
    View for vendor analytics and reporting.
    """
    # Check if the user is a vendor
    if not request.user.is_vendor or not hasattr(request.user, 'vendor'):
        messages.error(request, 'You need to register as a vendor to access the dashboard')
        return redirect('vendors:become_vendor')

    vendor = request.user.vendor

    context = {
        'vendor': vendor,
    }

    return render(request, 'vendors/dashboard/analytics.html', context)
