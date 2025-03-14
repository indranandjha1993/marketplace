from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import UserProfile, UserAddress
from products.models import Product


@login_required
def user_profile(request):
    """
    View for user profile management with enhanced order statistics.
    """
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    # Get basic order statistics
    from django.db.models import Count, Sum
    from orders.models import Order

    # Get order stats
    order_stats = {
        'total': Order.objects.filter(user=request.user).count(),
        'completed': Order.objects.filter(user=request.user, status='delivered').count(),
        'processing': Order.objects.filter(user=request.user, status__in=['pending', 'processing', 'shipped']).count(),
        'cancelled': Order.objects.filter(user=request.user, status='cancelled').count(),
        'total_spent': Order.objects.filter(user=request.user, status='delivered').aggregate(Sum('total'))[
                           'total__sum'] or 0,
    }

    # Get recent orders
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:3]

    if request.method == 'POST':
        # Enhanced security - verify current password before saving changes
        current_password = request.POST.get('current_password')
        if not current_password or not request.user.check_password(current_password):
            messages.error(request, 'Please enter your current password correctly to make changes')
            return redirect('accounts:user_profile')

        # Update user info
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.phone_number = request.POST.get('phone_number')

        # If user wants to change password
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password:
            if new_password == confirm_password:
                request.user.set_password(new_password)
                update_session_auth_hash(request, request.user)  # Keep user logged in
            else:
                messages.error(request, 'New passwords do not match')
                return redirect('accounts:user_profile')

        request.user.save()

        # Update profile
        profile.address_line1 = request.POST.get('address_line1')
        profile.address_line2 = request.POST.get('address_line2')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.country = request.POST.get('country')
        profile.postal_code = request.POST.get('postal_code')

        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']

        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:user_profile')

    context = {
        'profile': profile,
        'order_stats': order_stats,
        'recent_orders': recent_orders,
    }

    return render(request, 'accounts/user_profile.html', context)


@login_required
def user_addresses(request):
    """
    View for managing user addresses.
    """
    addresses = UserAddress.objects.filter(user=request.user)

    context = {
        'addresses': addresses
    }

    return render(request, 'accounts/user_addresses.html', context)


@login_required
def add_address(request):
    """
    View for adding a new address.
    """
    if request.method == 'POST':
        address_type = request.POST.get('address_type')
        is_default = request.POST.get('is_default') == 'on'

        address = UserAddress.objects.create(
            user=request.user,
            address_type=address_type,
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            address_line1=request.POST.get('address_line1'),
            address_line2=request.POST.get('address_line2', ''),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            country=request.POST.get('country'),
            postal_code=request.POST.get('postal_code'),
            is_default=is_default
        )

        messages.success(request, 'Address added successfully.')
        return redirect('accounts:user_addresses')

    return render(request, 'accounts/add_address.html')


@login_required
def edit_address(request, address_id):
    """
    View for editing an existing address.
    """
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)

    if request.method == 'POST':
        address.address_type = request.POST.get('address_type')
        address.full_name = request.POST.get('full_name')
        address.phone = request.POST.get('phone')
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2', '')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.country = request.POST.get('country')
        address.postal_code = request.POST.get('postal_code')
        address.is_default = request.POST.get('is_default') == 'on'

        address.save()
        messages.success(request, 'Address updated successfully.')
        return redirect('accounts:user_addresses')

    context = {
        'address': address
    }

    return render(request, 'accounts/edit_address.html', context)


@login_required
@require_POST
def delete_address(request, address_id):
    """
    View for deleting an address.
    """
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully.')
    return redirect('accounts:user_addresses')


@login_required
@require_POST
def set_default_address(request, address_id):
    """
    View for setting an address as default.
    """
    address = get_object_or_404(UserAddress, id=address_id, user=request.user)

    # Set all addresses of same type to non-default
    UserAddress.objects.filter(user=request.user, address_type=address.address_type).update(is_default=False)

    # Set this one as default
    address.is_default = True
    address.save()

    messages.success(request, 'Default address updated successfully.')
    return redirect('accounts:user_addresses')


@login_required
def wishlist(request):
    """
    View for displaying user's wishlist.
    """
    try:
        profile = request.user.profile
        wishlist_products = profile.wishlist_products.all()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
        wishlist_products = []

    context = {
        'wishlist_products': wishlist_products
    }

    return render(request, 'accounts/wishlist.html', context)


@login_required
@require_POST
def add_to_wishlist(request, product_id):
    """
    View for adding a product to wishlist.
    """
    product = get_object_or_404(Product, id=product_id)

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    profile.wishlist_products.add(product)
    messages.success(request, 'Product added to wishlist.')

    # Redirect back to the referring page
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('products:product_detail', product_slug=product.slug)


@login_required
@require_POST
def remove_from_wishlist(request, product_id):
    """
    View for removing a product from wishlist.
    """
    product = get_object_or_404(Product, id=product_id)

    try:
        profile = request.user.profile
        profile.wishlist_products.remove(product)
        messages.success(request, 'Product removed from wishlist.')
    except UserProfile.DoesNotExist:
        pass

    # Redirect back to the referring page
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('accounts:wishlist')


@login_required
@require_POST
def toggle_wishlist(request, product_id):
    """
    View for toggling a product in the wishlist (add if not present, remove if present).
    """
    product = get_object_or_404(Product, id=product_id)

    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    # Check if product is already in wishlist
    if product in profile.wishlist_products.all():
        # Remove from wishlist
        profile.wishlist_products.remove(product)
        status = 'removed'
        message = 'Product removed from wishlist.'
    else:
        # Add to wishlist
        profile.wishlist_products.add(product)
        status = 'added'
        message = 'Product added to wishlist.'

    # If this is an AJAX request, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': status,
            'message': message
        })

    # Otherwise, add message and redirect
    messages.success(request, message)

    # Redirect back to the referring page
    next_url = request.POST.get('next', '')
    if next_url:
        return redirect(next_url)
    return redirect('products:product_detail', product_slug=product.slug)
