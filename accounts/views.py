import stripe
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from orders.models import Order
from payments.models import PaymentMethod
from products.models import Product
from .models import UserProfile, UserAddress


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
    from django.db.models import Sum
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
        'page_title': 'My Profile',
        'active_tab': 'profile',
    }

    return render(request, 'accounts/user_profile.html', context)


@login_required
def user_addresses(request):
    """
    View for managing user addresses.
    """
    addresses = UserAddress.objects.filter(user=request.user)

    context = {
        'addresses': addresses,
        'page_title': 'My Addresses',
        'breadcrumb_active': 'My Addresses',
        'active_tab': 'addresses',
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

    context = {
        'page_title': 'Add New Address',
        'breadcrumb_active': 'Add Address',
        'active_tab': 'addresses',
    }

    return render(request, 'accounts/add_address.html', context)


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
        'wishlist_products': wishlist_products,
        'page_title': 'My Wishlist',
        'breadcrumb_active': 'My Wishlist',
        'active_tab': 'wishlist',
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


@login_required
def order_list(request):
    """
    Display list of user's orders.
    """
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'orders': orders,
        'page_title': 'My Orders',
        'breadcrumb_active': 'My Orders',
        'active_tab': 'orders',
    }

    return render(request, 'accounts/order_list.html', context)


@login_required
def order_detail(request, order_number):
    """
    Display order details.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    order_items = order.items.all()
    vendor_orders = order.vendor_orders.all()

    context = {
        'order': order,
        'order_items': order_items,
        'vendor_orders': vendor_orders,
        'page_title': 'Order Details',
        'breadcrumb_active': 'Orders Details',
        'active_tab': 'orders',
    }

    return render(request, 'accounts/order_detail.html', context)


@login_required
def payment_methods(request):
    """
    Display user's saved payment methods.
    """
    payment_methods = PaymentMethod.objects.filter(user=request.user)

    context = {
        'payment_methods': payment_methods,
        'page_title': 'Payment Methods',
        'breadcrumb_active': 'Payment Methods',
        'active_tab': 'payments',
    }

    return render(request, 'accounts/payment_methods.html', context)


@login_required
def add_payment_method(request):
    """
    Add a new payment method.
    """
    if request.method == 'POST':
        payment_type = request.POST.get('payment_type')

        if payment_type == 'card':
            # Process card information
            try:
                # Create Stripe token (in a real app, use Elements or Checkout)
                token = stripe.Token.create(
                    card={
                        'number': request.POST.get('card_number'),
                        'exp_month': int(request.POST.get('card_exp_month')),
                        'exp_year': int(request.POST.get('card_exp_year')),
                        'cvc': request.POST.get('card_cvc'),
                    },
                )

                # Create customer if not exists
                customer = None
                customer_id = request.user.profile.stripe_customer_id if hasattr(request.user, 'profile') and hasattr(
                    request.user.profile, 'stripe_customer_id') else None

                if customer_id:
                    try:
                        customer = stripe.Customer.retrieve(customer_id)
                    except:
                        customer = None

                if not customer:
                    customer = stripe.Customer.create(
                        email=request.user.email,
                        name=f"{request.user.first_name} {request.user.last_name}",
                    )
                    # Save customer ID to user profile
                    if hasattr(request.user, 'profile'):
                        request.user.profile.stripe_customer_id = customer.id
                        request.user.profile.save()

                # Add card to customer
                card = stripe.Customer.create_source(
                    customer.id,
                    source=token.id,
                )

                # Store card info in database
                payment_method = PaymentMethod.objects.create(
                    user=request.user,
                    payment_type='card',
                    provider='stripe',
                    card_last4=card.last4,
                    card_brand=card.brand,
                    card_exp_month=card.exp_month,
                    card_exp_year=card.exp_year,
                    token=card.id,
                    is_default=request.POST.get('is_default') == 'on'
                )

                messages.success(request, 'Payment method added successfully.')
                return redirect('accounts:payment_methods')

            except Exception as e:
                messages.error(request, f'Error adding card: {str(e)}')

        elif payment_type == 'bank':
            # Store bank account info
            PaymentMethod.objects.create(
                user=request.user,
                payment_type='bank',
                provider='direct',
                bank_name=request.POST.get('bank_name'),
                bank_account_last4=request.POST.get('bank_account_number')[-4:],
                is_default=request.POST.get('is_default') == 'on'
            )
            messages.success(request, 'Bank account added successfully.')
            return redirect('accounts:payment_methods')

        elif payment_type == 'upi':
            # Store UPI ID
            PaymentMethod.objects.create(
                user=request.user,
                payment_type='upi',
                provider='upi',
                upi_id=request.POST.get('upi_id'),
                is_default=request.POST.get('is_default') == 'on'
            )
            messages.success(request, 'UPI ID added successfully.')
            return redirect('accounts:payment_methods')

        elif payment_type == 'wallet':
            # Store wallet info
            PaymentMethod.objects.create(
                user=request.user,
                payment_type='wallet',
                provider=request.POST.get('wallet_provider'),
                wallet_name=request.POST.get('wallet_name'),
                wallet_id=request.POST.get('wallet_id'),
                is_default=request.POST.get('is_default') == 'on'
            )
            messages.success(request, 'Wallet added successfully.')
            return redirect('accounts:payment_methods')

        else:
            messages.error(request, 'Invalid payment method type.')

    context = {
        'page_title': 'Add Payment Method',
        'breadcrumb_active': 'Add Payment Method',
        'active_tab': 'payments',
    }

    return render(request, 'accounts/add_payment_method.html', context)


@login_required
@require_POST
def remove_payment_method(request, method_id):
    """
    Remove a saved payment method.
    """
    payment_method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)

    try:
        # If it's a Stripe card, remove from Stripe as well
        if payment_method.payment_type == 'card' and payment_method.provider == 'stripe' and payment_method.token:
            customer_id = request.user.profile.stripe_customer_id if hasattr(request.user, 'profile') and hasattr(
                request.user.profile, 'stripe_customer_id') else None

            if customer_id:
                stripe.Customer.delete_source(
                    customer_id,
                    payment_method.token
                )

        payment_method.delete()
        messages.success(request, 'Payment method removed successfully.')
    except Exception as e:
        messages.error(request, f'Error removing payment method: {str(e)}')

    return redirect('accounts:payment_methods')


@login_required
@require_POST
def set_default_payment_method(request, method_id):
    """
    Set a payment method as default.
    """
    payment_method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)

    # First, unset all other methods of the same type
    PaymentMethod.objects.filter(user=request.user, payment_type=payment_method.payment_type).update(is_default=False)

    # Set this one as default
    payment_method.is_default = True
    payment_method.save()

    messages.success(request, 'Default payment method updated.')
    return redirect('accounts:payment_methods')
