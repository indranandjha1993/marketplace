import logging

import razorpay
from django.conf import settings

from .base import PaymentGatewayService


class RazorpayService(PaymentGatewayService):
    """
    Razorpay payment gateway service implementation.
    
    This service handles:
    - Creating Razorpay orders
    - Verifying payment signatures
    - Fetching payment details
    """

    def _initialize(self):
        """
        Initialize the Razorpay client with API keys from settings.
        Sets app details for better tracking in Razorpay dashboard.
        """
        self.client = None
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET

        if self.key_id and self.key_secret:
            try:
                self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
                # Set app details for better tracking in Razorpay dashboard
                self.client.set_app_details({"title": "Marketplace", "version": "1.0.0"})
            except Exception as e:
                logging.error(f"Failed to initialize Razorpay client: {str(e)}")

    def is_configured(self):
        """
        Check if Razorpay is properly configured.
        
        Returns:
            bool: True if Razorpay is configured, False otherwise
        """
        return bool(self.key_id and self.key_secret and self.client)

    def create_payment(self, order, **kwargs):
        """
        Create a Razorpay order for the given marketplace order.
        
        Args:
            order: The order to create a payment for
            **kwargs: Additional arguments
            
        Returns:
            dict: Payment creation response with order_id, amount, and other data
                  needed for the frontend checkout
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Razorpay is not properly configured'
            }

        try:
            # Convert amount to paise (Razorpay uses smallest currency unit)
            amount = int(order.total * 100)
            currency = 'INR'

            # Create detailed notes for better tracking
            notes = {
                'order_number': order.order_number,
                'user_id': str(order.user.id),
                'user_email': order.user.email,
                'items_count': str(order.items.count()),
            }

            # Add shipping address details to notes if available
            if order.shipping_address:
                notes.update({
                    'shipping_name': order.shipping_address.full_name,
                    'shipping_city': order.shipping_address.city,
                    'shipping_state': order.shipping_address.state,
                    'shipping_country': order.shipping_address.country,
                })

            # Create Razorpay order
            razorpay_order = self.client.order.create({
                'amount': amount,
                'currency': currency,
                'receipt': order.order_number,
                'notes': notes,
                # Partial payments are disabled by default
                'partial_payment': False,
            })

            # Get user's phone number if available
            phone_number = ''
            if hasattr(order.user, 'phone_number') and order.user.phone_number:
                phone_number = order.user.phone_number
            elif order.shipping_address and order.shipping_address.phone:
                phone_number = order.shipping_address.phone
            elif order.billing_address and order.billing_address.phone:
                phone_number = order.billing_address.phone

            # Format phone number with country code if needed
            if phone_number and not phone_number.startswith('+'):
                phone_number = f"+91{phone_number}"  # Default to India country code

            # Prepare checkout options for frontend
            checkout_options = {
                'success': True,
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': currency,
                'merchant_key': self.key_id,
                'callback_url': self.get_callback_url(order.order_number),
                'prefill': {
                    'name': order.user.get_full_name() or order.user.email,
                    'email': order.user.email,
                    'contact': phone_number
                },
                # Additional checkout options for better UX
                'name': getattr(settings, 'SITE_NAME', 'Marketplace'),
                'description': f'Order #{order.order_number}',
                'theme': {
                    'color': '#3399cc'  # Customize as per your brand color
                },
                'modal': {
                    'escape': False,
                    'backdropclose': False,
                    'confirm_close': True,
                },
                'notes': notes
            }

            # Add image if available in settings
            if hasattr(settings, 'SITE_LOGO_URL') and settings.SITE_LOGO_URL:
                checkout_options['image'] = settings.SITE_LOGO_URL
            elif hasattr(settings, 'SITE_LOGO'):
                checkout_options['image'] = settings.SITE_LOGO

            return checkout_options

        except Exception as e:
            logging.error(f"Razorpay order creation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def verify_payment(self, order, **kwargs):
        """
        Verify a Razorpay payment for the given order.
        
        This method:
        1. Verifies the payment signature to ensure authenticity
        2. Fetches payment details to confirm status
        
        Args:
            order: The order to verify payment for
            **kwargs: Additional arguments including:
                - razorpay_payment_id: The Razorpay payment ID
                - razorpay_order_id: The Razorpay order ID
                - razorpay_signature: The Razorpay signature
            
        Returns:
            dict: Payment verification response with status and data
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Razorpay is not properly configured'
            }

        try:
            # Get payment details from kwargs
            payment_id = kwargs.get('razorpay_payment_id')
            order_id = kwargs.get('razorpay_order_id')
            signature = kwargs.get('razorpay_signature')

            # If we don't have all required parameters, return error
            if not (payment_id and order_id and signature):
                missing_params = []
                if not payment_id:
                    missing_params.append('razorpay_payment_id')
                if not order_id:
                    missing_params.append('razorpay_order_id')
                if not signature:
                    missing_params.append('razorpay_signature')

                return {
                    'success': False,
                    'error': f'Missing required payment parameters: {", ".join(missing_params)}'
                }

            # Verify signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            try:
                # Verify the payment signature
                self.client.utility.verify_payment_signature(params_dict)
            except Exception as e:
                logging.error(f"Payment signature verification failed: {str(e)}")
                return {
                    'success': False,
                    'verified': False,
                    'error': f'Invalid payment signature: {str(e)}'
                }

            # Get payment details
            try:
                payment_details = self.client.payment.fetch(payment_id)
            except Exception as e:
                logging.error(f"Failed to fetch payment details: {str(e)}")
                # If signature is verified but we can't fetch details, still consider it verified
                return {
                    'success': True,
                    'verified': True,
                    'payment_id': payment_id,
                    'order_id': order_id,
                    'signature': signature,
                    'error': f'Payment verified but details could not be fetched: {str(e)}'
                }

            # Check if payment is authorized or captured
            payment_status = payment_details.get('status', '')
            if payment_status not in ['authorized', 'captured']:
                return {
                    'success': False,
                    'verified': True,  # Signature is valid but payment is not successful
                    'payment_id': payment_id,
                    'order_id': order_id,
                    'status': payment_status,
                    'error': f'Payment is not successful. Status: {payment_status}'
                }

            # Return successful verification with payment details
            return {
                'success': True,
                'verified': True,
                'payment_id': payment_id,
                'order_id': order_id,
                'signature': signature,
                'amount': payment_details.get('amount', 0) / 100,  # Convert from paise to rupees
                'status': payment_status,
                'method': payment_details.get('method', ''),
                'payment_data': payment_details
            }
        except Exception as e:
            logging.error(f"Payment verification failed: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': str(e)
            }

    def fetch_payment(self, payment_id):
        """
        Fetch payment details from Razorpay.
        
        Args:
            payment_id: The Razorpay payment ID
            
        Returns:
            dict: Payment details or error
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Razorpay is not properly configured'
            }

        try:
            payment_details = self.client.payment.fetch(payment_id)
            return {
                'success': True,
                'payment_data': payment_details,
                'amount': payment_details.get('amount', 0) / 100,  # Convert from paise to rupees
                'status': payment_details.get('status', ''),
                'method': payment_details.get('method', ''),
            }
        except Exception as e:
            logging.error(f"Failed to fetch payment details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def refund_payment(self, payment_id, amount=None, notes=None):
        """
        Refund a payment.
        
        Args:
            payment_id: The Razorpay payment ID to refund
            amount: The amount to refund (in rupees). If None, full amount is refunded.
            notes: Additional notes for the refund
            
        Returns:
            dict: Refund details or error
        """
        if not self.is_configured():
            return {
                'success': False,
                'error': 'Razorpay is not properly configured'
            }

        try:
            refund_data = {}

            # If amount is specified, convert to paise
            if amount is not None:
                refund_data['amount'] = int(amount * 100)

            # Add notes if provided
            if notes:
                refund_data['notes'] = notes

            # Create refund
            refund = self.client.payment.refund(payment_id, refund_data)

            return {
                'success': True,
                'refund_id': refund['id'],
                'amount': refund.get('amount', 0) / 100,  # Convert from paise to rupees
                'status': refund.get('status', ''),
                'refund_data': refund
            }
        except Exception as e:
            logging.error(f"Payment refund failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
