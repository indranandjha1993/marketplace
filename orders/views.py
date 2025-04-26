import csv

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST

from accounts.models import UserAddress
from cart.models import Cart
from .models import Order, VendorOrder, OrderItem, Refund, OrderTracking, Coupon


@login_required
def checkout(request):
    """
    Display checkout page for user to complete order.
    """
    # Get user's cart
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:
            session_id = request.session.session_key
            cart = Cart.objects.get(session_id=session_id)

        # Ensure cart is not empty
        if cart.items.count() == 0:
            messages.warning(request, "Your cart is empty.")
            return redirect('cart:cart_detail')

    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    # Get user's saved addresses
    addresses = []
    default_shipping_address = None
    default_billing_address = None

    if request.user.is_authenticated:
        addresses = UserAddress.objects.filter(user=request.user)

        # Try to get default addresses
        try:
            default_shipping_address = addresses.filter(address_type__in=['shipping', 'both'], is_default=True).first()
        except UserAddress.DoesNotExist:
            pass

        try:
            default_billing_address = addresses.filter(address_type__in=['billing', 'both'], is_default=True).first()
        except UserAddress.DoesNotExist:
            pass

    # Check for coupon
    coupon_id = request.session.get('coupon_id')
    coupon = None
    coupon_discount = 0

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid:
                coupon_discount = coupon.calculate_discount(cart.subtotal)
            else:
                # Remove invalid coupon
                del request.session['coupon_id']
                messages.warning(request, 'The coupon has expired or is no longer valid')
                coupon = None
        except Coupon.DoesNotExist:
            del request.session['coupon_id']
            coupon = None

    context = {
        'cart': cart,
        'cart_items': cart.items.all(),
        'addresses': addresses,
        'default_shipping_address': default_shipping_address,
        'default_billing_address': default_billing_address,
        'coupon': coupon,
        'coupon_discount': coupon_discount,
        'subtotal': cart.subtotal,
        'tax_amount': cart.tax_amount,
        'shipping_cost': 0,  # This would typically be calculated based on address and products
        'total': cart.total - coupon_discount,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }

    return render(request, 'orders/checkout.html', context)


@login_required
@transaction.atomic
def place_order(request):
    """
    Process the order submission.
    """
    if request.method != 'POST':
        return redirect('orders:checkout')

    # Get user's cart
    try:
        cart = Cart.objects.get(user=request.user)
        if cart.items.count() == 0:
            messages.warning(request, "Your cart is empty.")
            return redirect('cart:cart_detail')
    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty.")
        return redirect('cart:cart_detail')

    # Get or create addresses
    shipping_address_id = request.POST.get('shipping_address')
    billing_address_id = request.POST.get('billing_address')
    use_shipping_for_billing = request.POST.get('use_shipping_for_billing') == 'on'

    # Get shipping address
    if shipping_address_id and shipping_address_id != 'new':
        shipping_address = get_object_or_404(UserAddress, id=shipping_address_id, user=request.user)
    else:
        # Create new shipping address
        shipping_address = UserAddress.objects.create(
            user=request.user,
            address_type='shipping',
            full_name=request.POST.get('shipping_full_name'),
            phone=request.POST.get('shipping_phone'),
            address_line1=request.POST.get('shipping_address_line1'),
            address_line2=request.POST.get('shipping_address_line2', ''),
            city=request.POST.get('shipping_city'),
            state=request.POST.get('shipping_state'),
            country=request.POST.get('shipping_country'),
            postal_code=request.POST.get('shipping_postal_code'),
            is_default=request.POST.get('shipping_set_default') == 'on'
        )

    # Get or create billing address
    if use_shipping_for_billing:
        billing_address = shipping_address
    elif billing_address_id and billing_address_id != 'new':
        billing_address = get_object_or_404(UserAddress, id=billing_address_id, user=request.user)
    else:
        # Create new billing address
        billing_address = UserAddress.objects.create(
            user=request.user,
            address_type='billing',
            full_name=request.POST.get('billing_full_name'),
            phone=request.POST.get('billing_phone'),
            address_line1=request.POST.get('billing_address_line1'),
            address_line2=request.POST.get('billing_address_line2', ''),
            city=request.POST.get('billing_city'),
            state=request.POST.get('billing_state'),
            country=request.POST.get('billing_country'),
            postal_code=request.POST.get('billing_postal_code'),
            is_default=request.POST.get('billing_set_default') == 'on'
        )

    # Get payment method
    payment_method = request.POST.get('payment_method')

    # Check coupon
    coupon_id = request.session.get('coupon_id')
    coupon = None
    coupon_discount = 0

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid:
                coupon_discount = coupon.calculate_discount(cart.subtotal)
            else:
                coupon = None
        except Coupon.DoesNotExist:
            coupon = None

    # Calculate totals
    subtotal = cart.subtotal
    tax_amount = cart.tax_amount
    shipping_cost = 0  # Calculate based on shipping method and address
    discount_amount = coupon_discount
    total = subtotal + tax_amount + shipping_cost - discount_amount

    # Create order
    order_number = f"ORD-{get_random_string(length=8, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"

    order = Order.objects.create(
        user=request.user,
        order_number=order_number,
        shipping_address=shipping_address,
        billing_address=billing_address,
        payment_method=payment_method,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        tax_amount=tax_amount,
        discount_amount=discount_amount,
        total=total,
        coupon=coupon,
        status='pending',
        payment_status='pending'
    )

    # Create order items and vendor orders
    vendor_orders = {}

    for cart_item in cart.items.select_related('product', 'product__vendor').all():
        product = cart_item.product
        variant = cart_item.variant
        quantity = cart_item.quantity
        price = cart_item.unit_price
        tax_rate = cart_item.tax_rate
        tax_amount = cart_item.tax_amount
        total_item = cart_item.total

        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            quantity=quantity,
            price=price,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total=total_item
        )

        # Create or update vendor order
        vendor = product.vendor
        if vendor.id not in vendor_orders:
            # Calculate commission
            vendor_subtotal = price * quantity
            vendor_tax = tax_amount
            vendor_commission = round(vendor_subtotal * (vendor.commission_rate / 100), 2)
            vendor_amount = vendor_subtotal + vendor_tax - vendor_commission

            vendor_orders[vendor.id] = VendorOrder.objects.create(
                order=order,
                vendor=vendor,
                subtotal=vendor_subtotal,
                shipping_cost=0,  # Would be calculated based on items and shipping method
                tax_amount=vendor_tax,
                commission_amount=vendor_commission,
                total_vendor_amount=vendor_amount,
                status='pending'
            )
        else:
            # Update existing vendor order
            vendor_order = vendor_orders[vendor.id]
            vendor_subtotal = price * quantity
            vendor_tax = tax_amount
            vendor_commission = round(vendor_subtotal * (vendor.commission_rate / 100), 2)

            vendor_order.subtotal += vendor_subtotal
            vendor_order.tax_amount += vendor_tax
            vendor_order.commission_amount += vendor_commission
            vendor_order.total_vendor_amount += (vendor_subtotal + vendor_tax - vendor_commission)
            vendor_order.save()

    # Create order tracking for each vendor
    for vendor_order in vendor_orders.values():
        OrderTracking.objects.create(
            vendor_order=vendor_order,
            status='pending',
            comment='Order placed',
            updated_by=request.user
        )

    # If coupon was used, increment usage count and remove from session
    if coupon:
        coupon.usage_count += 1
        coupon.save()
        if 'coupon_id' in request.session:
            del request.session['coupon_id']

    # Clear the cart
    cart.clear()

    # send_order_confirmation_email(order)

    # Handle payment based on method
    if payment_method == 'cod':
        # For Cash on Delivery, just redirect to success page
        return redirect('orders:order_success', order_number=order_number)
    elif payment_method == 'stripe':
        # For Stripe, redirect to payment processing
        return redirect('payments:process_payment', order_number=order_number)
    elif payment_method == 'razorpay':
        # For Razorpay, redirect to payment processing
        return redirect('payments:process_payment', order_number=order_number)
    else:
        # Default fallback
        return redirect('orders:order_success', order_number=order_number)


@login_required
def order_success(request, order_number):
    """
    Display order success page.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    context = {
        'order': order
    }

    return render(request, 'orders/order_success.html', context)


@login_required
@require_POST
def cancel_order(request, order_number):
    """
    Cancel an order if it's still pending.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Check if order can be cancelled
    if order.status not in ['pending', 'processing']:
        messages.error(request, "This order cannot be cancelled.")
        return redirect('orders:order_detail', order_number=order_number)

    # Update order status
    order.status = 'cancelled'
    order.save()

    # Update vendor orders
    for vendor_order in order.vendor_orders.all():
        vendor_order.status = 'cancelled'
        vendor_order.save()

        # Add tracking entry
        OrderTracking.objects.create(
            vendor_order=vendor_order,
            status='cancelled',
            comment='Order cancelled by customer',
            updated_by=request.user
        )

    # Handle refund if payment was made
    if order.payment_status == 'paid':
        order.payment_status = 'refunded'
        order.save()

        # Create refund record
        Refund.objects.create(
            order=order,
            amount=order.total,
            reason='Order cancelled by customer',
            status='approved'
        )

    messages.success(request, "Your order has been cancelled successfully.")
    return redirect('orders:order_detail', order_number=order_number)


@login_required
@require_POST
def return_order(request, order_number):
    """
    Request a return for delivered order.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Check if order can be returned
    if order.status != 'delivered':
        messages.error(request, "Only delivered orders can be returned.")
        return redirect('orders:order_detail', order_number=order_number)

    # Check return window (e.g., 14 days)
    return_window_days = 14
    delivery_date = None

    # Find delivery date from tracking
    for vendor_order in order.vendor_orders.all():
        if vendor_order.delivery_date:
            if not delivery_date or vendor_order.delivery_date > delivery_date:
                delivery_date = vendor_order.delivery_date

    if delivery_date and (timezone.now() - delivery_date).days > return_window_days:
        messages.error(request, f"Return window of {return_window_days} days has passed.")
        return redirect('orders:order_detail', order_number=order_number)

    reason = request.POST.get('return_reason')

    if not reason:
        messages.error(request, "Please provide a reason for the return.")
        return redirect('orders:order_detail', order_number=order_number)

    # Update order status
    order.status = 'refunded'
    order.save()

    # Update vendor orders
    for vendor_order in order.vendor_orders.all():
        vendor_order.status = 'refunded'
        vendor_order.save()

        # Add tracking entry
        OrderTracking.objects.create(
            vendor_order=vendor_order,
            status='refunded',
            comment=f'Return requested by customer. Reason: {reason}',
            updated_by=request.user
        )

    # Create refund record
    Refund.objects.create(
        order=order,
        amount=order.total,
        reason=reason,
        status='pending'
    )

    messages.success(request, "Your return request has been submitted successfully.")
    return redirect('orders:order_detail', order_number=order_number)


@login_required
def track_order(request, order_number):
    """
    Track order status and delivery progress.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    vendor_orders = order.vendor_orders.all()

    tracking_history = []

    for vendor_order in vendor_orders:
        history = vendor_order.tracking_history.all().order_by('timestamp')
        tracking_history.append({
            'vendor': vendor_order.vendor,
            'vendor_order': vendor_order,
            'history': history
        })

    context = {
        'order': order,
        'tracking_history': tracking_history
    }

    return render(request, 'orders/track_order.html', context)


@login_required
def generate_invoice(request, order_number):
    """
    Generate and download invoice for an order.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # For simplicity, we're generating a CSV invoice
    # In a real application, you would generate a PDF using a library like ReportLab

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{order_number}_invoice.csv"'

    writer = csv.writer(response)
    writer.writerow(['Invoice for Order', order_number])
    writer.writerow(['Date', order.created_at.strftime('%Y-%m-%d')])
    writer.writerow(['Customer', f"{request.user.first_name} {request.user.last_name}"])
    writer.writerow(['Email', request.user.email])
    writer.writerow([])
    writer.writerow(['Product', 'Quantity', 'Price', 'Tax', 'Total'])

    for item in order.items.all():
        writer.writerow([
            item.product.title,
            item.quantity,
            item.price,
            item.tax_amount,
            item.total
        ])

    writer.writerow([])
    writer.writerow(['Subtotal', '', '', '', order.subtotal])
    writer.writerow(['Shipping', '', '', '', order.shipping_cost])
    writer.writerow(['Tax', '', '', '', order.tax_amount])

    if order.discount_amount > 0:
        writer.writerow(['Discount', '', '', '', f"-{order.discount_amount}"])

    writer.writerow(['Total', '', '', '', order.total])

    return response
