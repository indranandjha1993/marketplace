import stripe
from django.conf import settings

from .base import PaymentGatewayService


class StripeService(PaymentGatewayService):
    """
    Stripe payment gateway service implementation.
    """

    def _initialize(self):
        """
        Initialize the Stripe client.
        """
        self.api_key = settings.STRIPE_SECRET_KEY
        self.public_key = settings.STRIPE_PUBLIC_KEY

        if self.api_key:
            stripe.api_key = self.api_key
            # Set API version to the latest version
            stripe.api_version = "2023-10-16"

    def is_configured(self):
        """
        Check if Stripe is properly configured.
        
        Returns:
            bool: True if Stripe is configured, False otherwise
        """
        return bool(self.api_key and self.public_key)

    def create_payment(self, order, **kwargs):
        """
        Create a Stripe payment for the given order.
        
        Args:
            order: The order to create a payment for
            **kwargs: Additional arguments
            
        Returns:
            dict: Payment creation response with session_id, url, and other data
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Stripe is not properly configured'
            }

        try:
            # For Indian regulations, we'll let Stripe collect the address information
            # during checkout, so we don't need to validate addresses here

            success_url = self.get_success_url(order.order_number)
            cancel_url = self.get_cancel_url(order.order_number)

            # Add session_id parameter to success URL
            if '?' in success_url:
                success_url += '&session_id={CHECKOUT_SESSION_ID}'
            else:
                success_url += '?session_id={CHECKOUT_SESSION_ID}'

            # Create line items for Stripe
            line_items = []
            for item in order.items.all():
                product_name = item.product.title
                if item.variant:
                    variant_str = ", ".join(
                        [f"{val.attribute.name}: {val.value}" for val in item.variant.attribute_values.all()]
                    )
                    product_name += f" ({variant_str})"

                line_items.append({
                    'price_data': {
                        'currency': 'inr',
                        'product_data': {
                            'name': product_name,
                        },
                        'unit_amount': int(item.price * 100),  # Convert to smallest currency unit
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

            # We'll let Stripe collect address information during checkout
            # This is the recommended approach for Indian regulations

            # Create checkout session with proper parameters for Indian regulations
            session_params = {
                'customer_email': order.user.email,
                'payment_method_types': ['card'],
                'line_items': line_items,
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': {
                    'order_number': order.order_number,
                    'user_id': str(order.user.id),
                }
            }

            # Add discounts if any
            if discounts:
                session_params['discounts'] = discounts

            # Enable billing address collection (required for Indian regulations)
            session_params['billing_address_collection'] = 'required'

            # Enable shipping address collection if selling physical goods
            session_params['shipping_address_collection'] = {
                'allowed_countries': ['IN', 'US', 'CA', 'GB', 'AU', 'DE', 'FR', 'IT', 'ES', 'JP', 'SG']
            }

            # Enable phone number collection (helpful for Indian regulations)
            session_params['phone_number_collection'] = {
                'enabled': True
            }

            # Add payment intent data with description (required for Indian regulations)
            # Create a detailed description of the order items
            items_description = ", ".join([f"{item.quantity}x {item.product.title}" for item in order.items.all()[:3]])
            if order.items.count() > 3:
                items_description += f" and {order.items.count() - 3} more items"

            session_params['payment_intent_data'] = {
                'description': f'Order #{order.order_number}: {items_description}',
                'metadata': {
                    'order_id': order.order_number,
                }
            }

            # Create the checkout session
            checkout_session = stripe.checkout.Session.create(**session_params)

            return {
                'success': True,
                'session_id': checkout_session.id,
                'url': checkout_session.url,
                'public_key': self.public_key
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # We're letting Stripe handle country codes now

    def verify_payment(self, order, **kwargs):
        """
        Verify a Stripe payment for the given order.
        
        Args:
            order: The order to verify payment for
            **kwargs: Additional arguments including:
                - session_id: The Stripe session ID
            
        Returns:
            dict: Payment verification response with status and data
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Stripe is not properly configured'
            }

        try:
            session_id = kwargs.get('session_id')

            if not session_id:
                return {
                    'success': False,
                    'error': 'Missing session ID'
                }

            # Retrieve the session
            session = stripe.checkout.Session.retrieve(session_id)

            # Check if payment was successful
            if session.payment_status == 'paid':
                # Get the payment intent
                payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent)

                return {
                    'success': True,
                    'verified': True,
                    'session_id': session_id,
                    'payment_intent': session.payment_intent,
                    'amount': payment_intent.amount / 100,  # Convert from smallest currency unit
                    'status': payment_intent.status,
                    'payment_method': payment_intent.payment_method_types[
                        0] if payment_intent.payment_method_types else 'unknown',
                    'payment_data': payment_intent
                }
            else:
                return {
                    'success': True,
                    'verified': False,
                    'status': session.payment_status,
                    'error': 'Payment not completed'
                }
        except Exception as e:
            return {
                'success': False,
                'verified': False,
                'error': str(e)
            }
