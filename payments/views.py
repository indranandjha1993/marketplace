import razorpay
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from orders.models import Order, Payment
from .models import PaymentMethod, Transaction

# Initialize payment gateways
stripe.api_key = settings.STRIPE_SECRET_KEY
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required
def process_payment(request, order_number):
    """
    Process payment for an order based on the chosen payment method.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Check if payment is already completed
    if order.payment_status == 'paid':
        messages.info(request, 'Payment has already been completed for this order.')
        return redirect('orders:order_detail', order_number=order_number)

    # Check payment method
    payment_method = order.payment_method

    if payment_method == 'cod':
        # Cash on Delivery - mark as pending payment
        order.payment_status = 'pending'
        order.save()
        return redirect('orders:order_success', order_number=order_number)

    elif payment_method == 'stripe':
        # Create Stripe payment session
        try:
            success_url = request.build_absolute_uri(
                reverse('payments:verify_payment', args=[order_number])
            )
            cancel_url = request.build_absolute_uri(
                reverse('payments:payment_failed', args=[order_number])
            )

            # Create line items for Stripe
            line_items = []
            for item in order.items.all():
                product_name = item.product.title
                if item.variant:
                    variant_str = ", ".join(
                        [f"{val.attribute.name}: {val.value}" for val in item.variant.attribute_values.all()])
                    product_name += f" ({variant_str})"

                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': product_name,
                        },
                        'unit_amount': int(item.price * 100),  # Convert to paise (Stripe uses smallest currency unit)
                    },
                    'quantity': item.quantity,
                })

            # Add shipping and tax as separate line items if needed
            if order.shipping_cost > 0:
                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': 'Shipping',
                        },
                        'unit_amount': int(order.shipping_cost * 100),
                    },
                    'quantity': 1,
                })

            if order.tax_amount > 0:
                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': 'Tax',
                        },
                        'unit_amount': int(order.tax_amount * 100),
                    },
                    'quantity': 1,
                })

            # Apply discount if any
            discounts = []
            if order.discount_amount > 0:
                discounts.append({
                    'coupon': {
                        'name': 'Discount',
                        'amount_off': int(order.discount_amount * 100),
                        'currency': 'inr',
                        'duration': 'once',
                    }
                })

            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                customer_email=request.user.email,
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url,
                discounts=discounts,
                metadata={
                    'order_number': order.order_number,
                    'user_id': request.user.id,
                }
            )

            # Store session ID in the session for verification
            request.session['stripe_session_id'] = checkout_session.id

            # Create Transaction record
            Transaction.objects.create(
                order=order,
                user=request.user,
                amount=order.total,
                status='pending',
                transaction_type='payment',
                payment_method='stripe',
                provider='stripe',
                provider_transaction_id=checkout_session.id,
                metadata={
                    'checkout_session_id': checkout_session.id,
                }
            )

            # Redirect to Stripe Checkout
            return redirect(checkout_session.url)

        except Exception as e:
            messages.error(request, f'Error processing Stripe payment: {str(e)}')
            return redirect('payments:payment_failed', order_number=order_number)

    elif payment_method == 'razorpay':
        # Create Razorpay order
        try:
            razorpay_order_amount = int(order.total * 100)  # Convert to paise
            razorpay_order_currency = 'INR'

            # Create Razorpay order
            razorpay_order = razorpay_client.order.create({
                'amount': razorpay_order_amount,
                'currency': razorpay_order_currency,
                'receipt': order.order_number,
                'notes': {
                    'order_number': order.order_number,
                    'user_id': str(request.user.id),
                }
            })

            # Create Transaction record
            Transaction.objects.create(
                order=order,
                user=request.user,
                amount=order.total,
                status='pending',
                transaction_type='payment',
                payment_method='razorpay',
                provider='razorpay',
                provider_transaction_id=razorpay_order['id'],
                metadata={
                    'razorpay_order_id': razorpay_order['id'],
                }
            )

            # Store order ID in session for verification
            request.session['razorpay_order_id'] = razorpay_order['id']

            # Render Razorpay payment form
            context = {
                'order': order,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                'razorpay_amount': razorpay_order_amount,
                'currency': razorpay_order_currency,
                'callback_url': request.build_absolute_uri(reverse('payments:verify_payment', args=[order_number])),
                'razorpay_callback_url': request.build_absolute_uri(
                    reverse('payments:verify_payment', args=[order_number])),
            }

            return render(request, 'payments/razorpay_checkout.html', context)

        except Exception as e:
            messages.error(request, f'Error processing Razorpay payment: {str(e)}')
            return redirect('payments:payment_failed', order_number=order_number)

    else:
        # Unsupported payment method
        messages.error(request, 'Unsupported payment method.')
        return redirect('orders:checkout')


@login_required
def verify_payment(request, order_number):
    """
    Verify payment after it has been processed by the payment gateway.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Check payment method
    payment_method = order.payment_method

    if payment_method == 'stripe':
        # Verify Stripe payment
        session_id = request.GET.get('session_id')
        stored_session_id = request.session.get('stripe_session_id')

        if not session_id or session_id != stored_session_id:
            messages.error(request, 'Invalid payment session.')
            return redirect('payments:payment_failed', order_number=order_number)

        try:
            # Retrieve checkout session
            checkout_session = stripe.checkout.Session.retrieve(session_id)

            # Check if payment was successful
            if checkout_session.payment_status == 'paid':
                # Update order status
                with transaction.atomic():
                    order.payment_status = 'paid'
                    order.transaction_id = checkout_session.payment_intent
                    order.status = 'processing'
                    order.save()

                    # Update vendor orders
                    for vendor_order in order.vendor_orders.all():
                        vendor_order.status = 'processing'
                        vendor_order.save()

                        # Add tracking entry
                        vendor_order.tracking_history.create(
                            status='processing',
                            comment='Payment received, processing order',
                            updated_by=request.user
                        )

                    # Create payment record
                    Payment.objects.create(
                        order=order,
                        amount=order.total,
                        provider='stripe',
                        status='completed',
                        transaction_id=checkout_session.payment_intent,
                        payment_method='credit_card',
                        payment_data={
                            'session_id': session_id,
                            'payment_intent': checkout_session.payment_intent,
                        }
                    )

                    # Update transaction record
                    transaction = Transaction.objects.get(
                        order=order,
                        provider='stripe',
                        provider_transaction_id=session_id
                    )
                    transaction.status = 'completed'
                    transaction.updated_at = timezone.now()
                    transaction.save()

                # Clean up session
                if 'stripe_session_id' in request.session:
                    del request.session['stripe_session_id']

                messages.success(request, 'Payment successful! Your order is being processed.')
                return redirect('payments:payment_success', order_number=order_number)
            else:
                messages.error(request, 'Payment was not completed.')
                return redirect('payments:payment_failed', order_number=order_number)

        except Exception as e:
            messages.error(request, f'Error verifying payment: {str(e)}')
            return redirect('payments:payment_failed', order_number=order_number)

    elif payment_method == 'razorpay':
        # Verify Razorpay payment
        try:
            # Check if this is a callback from Razorpay
            if request.method == 'POST':
                razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
                razorpay_order_id = request.POST.get('razorpay_order_id', '')
                razorpay_signature = request.POST.get('razorpay_signature', '')

                # Verify signature
                params_dict = {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature
                }

                # Verify payment signature
                razorpay_client.utility.verify_payment_signature(params_dict)

                # If we get here, signature is valid
                with transaction.atomic():
                    order.payment_status = 'paid'
                    order.transaction_id = razorpay_payment_id
                    order.status = 'processing'
                    order.save()

                    # Update vendor orders
                    for vendor_order in order.vendor_orders.all():
                        vendor_order.status = 'processing'
                        vendor_order.save()

                        # Add tracking entry
                        vendor_order.tracking_history.create(
                            status='processing',
                            comment='Payment received, processing order',
                            updated_by=request.user
                        )

                    # Create payment record
                    Payment.objects.create(
                        order=order,
                        amount=order.total,
                        provider='razorpay',
                        status='completed',
                        transaction_id=razorpay_payment_id,
                        payment_method='razorpay',
                        payment_data={
                            'order_id': razorpay_order_id,
                            'payment_id': razorpay_payment_id,
                            'signature': razorpay_signature,
                        }
                    )

                    # Update transaction record
                    transaction = Transaction.objects.get(
                        order=order,
                        provider='razorpay',
                        provider_transaction_id=razorpay_order_id
                    )
                    transaction.status = 'completed'
                    transaction.updated_at = timezone.now()
                    transaction.save()

                # Clean up session
                if 'razorpay_order_id' in request.session:
                    del request.session['razorpay_order_id']

                messages.success(request, 'Payment successful! Your order is being processed.')
                return redirect('payments:payment_success', order_number=order_number)
            else:
                # If not a POST, check for GET redirect from Razorpay
                return render(request, 'payments/verify_razorpay.html', {'order': order})

        except Exception as e:
            messages.error(request, f'Error verifying Razorpay payment: {str(e)}')
            return redirect('payments:payment_failed', order_number=order_number)

    else:
        # Unsupported payment method or already verified
        return redirect('orders:order_detail', order_number=order_number)


@login_required
def payment_success(request, order_number):
    """
    Display payment success page.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    context = {
        'order': order,
    }

    return render(request, 'payments/payment_success.html', context)


@login_required
def payment_failed(request, order_number):
    """
    Display payment failed page.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    context = {
        'order': order,
    }

    return render(request, 'payments/payment_failed.html', context)


@login_required
def payment_methods(request):
    """
    Display user's saved payment methods.
    """
    payment_methods = PaymentMethod.objects.filter(user=request.user)

    context = {
        'payment_methods': payment_methods,
    }

    return render(request, 'payments/payment_methods.html', context)


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
                return redirect('payments:payment_methods')

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
            return redirect('payments:payment_methods')

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
            return redirect('payments:payment_methods')

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
            return redirect('payments:payment_methods')

        else:
            messages.error(request, 'Invalid payment method type.')

    return render(request, 'payments/add_payment_method.html')


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

    return redirect('payments:payment_methods')


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
    return redirect('payments:payment_methods')
