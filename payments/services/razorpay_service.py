import razorpay
from django.conf import settings

from .base import PaymentGatewayService


class RazorpayService(PaymentGatewayService):
    """
    Razorpay payment gateway service implementation.
    """

    def _initialize(self):
        """
        Initialize the Razorpay client.
        """
        self.client = None
        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
            self.client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

    def is_configured(self):
        """
        Check if Razorpay is properly configured.
        
        Returns:
            bool: True if Razorpay is configured, False otherwise
        """
        return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET and self.client)

    def create_payment(self, order, **kwargs):
        """
        Create a Razorpay payment for the given order.
        
        Args:
            order: The order to create a payment for
            **kwargs: Additional arguments
            
        Returns:
            dict: Payment creation response with order_id, amount, and other data
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

            # Create Razorpay order
            razorpay_order = self.client.order.create({
                'amount': amount,
                'currency': currency,
                'receipt': order.order_number,
                'notes': {
                    'order_number': order.order_number,
                    'user_id': str(order.user.id),
                }
            })

            return {
                'success': True,
                'order_id': razorpay_order['id'],
                'amount': amount,
                'currency': currency,
                'merchant_key': settings.RAZORPAY_KEY_ID,
                'callback_url': self.get_callback_url(order.order_number),
                'prefill': {
                    'name': order.user.get_full_name() or order.user.email,
                    'email': order.user.email,
                    'contact': getattr(order.user, 'phone_number', '') or ''
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def verify_payment(self, order, **kwargs):
        """
        Verify a Razorpay payment for the given order.
        
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
                return {
                    'success': False,
                    'error': 'Missing required payment parameters'
                }

            # Verify signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            # Verify the payment signature
            self.client.utility.verify_payment_signature(params_dict)

            # Get payment details
            payment_details = self.client.payment.fetch(payment_id)

            return {
                'success': True,
                'verified': True,
                'payment_id': payment_id,
                'order_id': order_id,
                'signature': signature,
                'amount': payment_details.get('amount', 0) / 100,  # Convert from paise to rupees
                'status': payment_details.get('status', ''),
                'method': payment_details.get('method', ''),
                'payment_data': payment_details
            }
        except Exception as e:
            return {
                'success': False,
                'verified': False,
                'error': str(e)
            }
