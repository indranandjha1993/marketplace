from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from orders.models import Order, Payment
from .models import Transaction
from .services.factory import PaymentServiceFactory


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

    # Get payment method
    payment_method = order.payment_method

    # Get the appropriate payment service
    payment_service = PaymentServiceFactory.get_service(payment_method, request)

    if not payment_service:
        messages.error(request, f'Unsupported payment method: {payment_method}')
        return redirect('orders:checkout')

    if not payment_service.is_configured() and payment_method != 'cod':
        messages.error(
            request,
            f'{PaymentServiceFactory.get_display_name(payment_method)} is not properly configured. '
            'Please try a different payment method.'
        )
        return redirect('orders:checkout')

    try:
        # Process the payment
        result = payment_service.create_payment(order)

        if not result['success']:
            messages.error(request, f'Error processing payment: {result.get("error", "Unknown error")}')
            return redirect('payments:payment_failed', order_number=order_number)

        # Handle Cash on Delivery
        if payment_method == 'cod':
            order.payment_status = 'pending'
            order.save()
            return redirect('orders:order_success', order_number=order_number)

        # Handle Stripe
        elif payment_method == 'stripe':
            # Create Transaction record
            Transaction.objects.create(
                order=order,
                user=request.user,
                amount=order.total,
                status='pending',
                transaction_type='payment',
                payment_method='stripe',
                provider='stripe',
                provider_transaction_id=result['session_id'],
                metadata={
                    'checkout_session_id': result['session_id'],
                }
            )

            # Store session ID in the session for verification
            request.session['stripe_session_id'] = result['session_id']

            # Redirect to Stripe Checkout
            return redirect(result['url'])

        # Handle Razorpay
        elif payment_method == 'razorpay':
            # Create Transaction record
            Transaction.objects.create(
                order=order,
                user=request.user,
                amount=order.total,
                status='pending',
                transaction_type='payment',
                payment_method='razorpay',
                provider='razorpay',
                provider_transaction_id=result['order_id'],
                metadata={
                    'razorpay_order_id': result['order_id'],
                }
            )

            # Store order ID in session for verification
            request.session['razorpay_order_id'] = result['order_id']

            # Render Razorpay payment form
            context = {
                'order': order,
                'razorpay_order_id': result['order_id'],
                'razorpay_merchant_key': result['merchant_key'],
                'razorpay_amount': result['amount'],
                'currency': result['currency'],
                'callback_url': result['callback_url'],
                'prefill': result.get('prefill', {})
            }

            return render(request, 'payments/razorpay_checkout.html', context)

        # Handle other payment methods
        else:
            messages.error(request, f'Unsupported payment method: {payment_method}')
            return redirect('orders:checkout')

    except Exception as e:
        print(f"Payment processing error: {str(e)}")
        messages.error(request, f'Error processing payment: {str(e)}')
        return redirect('payments:payment_failed', order_number=order_number)


@login_required
def verify_payment(request, order_number):
    """
    Verify payment after it has been processed by the payment gateway.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # If it's an AJAX request and the payment is already verified, redirect to success
    if is_ajax and order.payment_status == 'paid':
        return redirect('payments:payment_success', order_number=order_number)

    # Get payment method
    payment_method = order.payment_method

    # Get the appropriate payment service
    payment_service = PaymentServiceFactory.get_service(payment_method, request)

    if not payment_service:
        messages.error(request, f'Unsupported payment method: {payment_method}')
        return redirect('payments:payment_failed', order_number=order_number)

    # Handle Cash on Delivery
    if payment_method == 'cod':
        return redirect('orders:order_detail', order_number=order_number)

    # Handle Stripe
    elif payment_method == 'stripe':
        # Get session ID from query params or session
        session_id = request.GET.get('session_id') or request.session.get('stripe_session_id')

        if not session_id:
            messages.error(request, 'No Stripe session ID found.')
            return redirect('payments:payment_failed', order_number=order_number)

        # Verify payment
        result = payment_service.verify_payment(order, session_id=session_id)

        if not result['success']:
            messages.error(request, f'Error verifying payment: {result.get("error", "Unknown error")}')
            return redirect('payments:payment_failed', order_number=order_number)

        if not result.get('verified', False):
            messages.error(request, f'Payment not completed. Status: {result.get("status", "unknown")}')
            return redirect('payments:payment_failed', order_number=order_number)

        # Update order and create payment record
        try:
            with db_transaction.atomic():
                # Update order status
                order.payment_status = 'paid'
                order.transaction_id = result['payment_intent']
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
                payment = Payment.objects.create(
                    order=order,
                    amount=order.total,
                    provider='stripe',
                    status='completed',
                    transaction_id=result['payment_intent'],
                    payment_method='stripe',
                    payment_data=result.get('payment_data', {})
                )

                # Update transaction record
                try:
                    transaction = Transaction.objects.get(
                        order=order,
                        provider='stripe',
                        provider_transaction_id=session_id
                    )
                    transaction.status = 'completed'
                    transaction.updated_at = timezone.now()
                    transaction.save()
                except Transaction.DoesNotExist:
                    Transaction.objects.create(
                        order=order,
                        user=request.user,
                        amount=order.total,
                        status='completed',
                        transaction_type='payment',
                        payment_method='stripe',
                        provider='stripe',
                        provider_transaction_id=result['payment_intent'],
                        metadata={
                            'session_id': session_id,
                        }
                    )
        except Exception as db_error:
            messages.error(request, f"Error processing payment: {str(db_error)}")
            return redirect('payments:payment_failed', order_number=order_number)

        # Clean up session
        if 'stripe_session_id' in request.session:
            del request.session['stripe_session_id']

        # Success message and redirect
        messages.success(request, 'Payment successful! Your order is being processed.')
        return redirect('payments:payment_success', order_number=order_number)

    # Handle Razorpay
    elif payment_method == 'razorpay':
        # Get Razorpay order ID from session
        razorpay_order_id = request.session.get('razorpay_order_id')

        if not razorpay_order_id:
            messages.error(request, 'No Razorpay order ID found.')
            return redirect('payments:payment_failed', order_number=order_number)

        # If this is a POST request, it's a callback from Razorpay
        if request.method == 'POST':
            # Get payment details from POST data
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_signature = request.POST.get('razorpay_signature')

            # Verify payment
            result = payment_service.verify_payment(
                order,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature
            )

            if not result['success'] or not result.get('verified', False):
                messages.error(request, f'Error verifying payment: {result.get("error", "Unknown error")}')
                return redirect('payments:payment_failed', order_number=order_number)

            # Update order and create payment record
            try:
                with db_transaction.atomic():
                    # Update order status
                    order.payment_status = 'paid'
                    order.transaction_id = razorpay_payment_id
                    order.status = 'processing'
                    order.save()
                    print(f"Order {order.order_number} updated to paid status")

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
                    print("Vendor orders updated")

                    # Create payment record
                    payment = Payment.objects.create(
                        order=order,
                        amount=order.total,
                        provider='razorpay',
                        status='completed',
                        transaction_id=razorpay_payment_id,
                        payment_method='razorpay',
                        payment_data=result.get('payment_data', {})
                    )
                    print(f"Payment record created: {payment.id}")

                    # Update transaction record
                    try:
                        transaction = Transaction.objects.get(
                            order=order,
                            provider='razorpay',
                            provider_transaction_id=razorpay_order_id
                        )
                        transaction.status = 'completed'
                        transaction.updated_at = timezone.now()
                        transaction.save()
                        print(f"Transaction record updated: {transaction.id}")
                    except Transaction.DoesNotExist:
                        print("Transaction record not found, creating new one")
                        Transaction.objects.create(
                            order=order,
                            user=request.user,
                            amount=order.total,
                            status='completed',
                            transaction_type='payment',
                            payment_method='razorpay',
                            provider='razorpay',
                            provider_transaction_id=razorpay_payment_id,
                            metadata={
                                'razorpay_order_id': razorpay_order_id,
                                'razorpay_payment_id': razorpay_payment_id,
                            }
                        )
            except Exception as db_error:
                print(f"Database transaction error: {str(db_error)}")
                messages.error(request, f"Error processing payment: {str(db_error)}")
                return redirect('payments:payment_failed', order_number=order_number)

            # Clean up session
            if 'razorpay_order_id' in request.session:
                del request.session['razorpay_order_id']
                print("Razorpay order ID removed from session")

            # Success message and redirect
            messages.success(request, 'Payment successful! Your order is being processed.')
            print(f"Payment successful for order {order.order_number}")
            return redirect('payments:payment_success', order_number=order_number)
        else:
            # If not a POST, show the verification page
            print(f"GET request to verify_payment for order {order.order_number}")

            # If it's an AJAX request, return a 200 status to indicate the payment is still being processed
            if is_ajax:
                return HttpResponse(status=200)

            return render(request, 'payments/verify_razorpay.html', {'order': order})

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
