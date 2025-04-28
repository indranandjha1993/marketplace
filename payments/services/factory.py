from .cod_service import CashOnDeliveryService
from .razorpay_service import RazorpayService
from .stripe_service import StripeService


class PaymentServiceFactory:
    """
    Factory class to get the appropriate payment service.
    """

    @staticmethod
    def get_service(payment_method, request=None):
        """
        Get the payment service for the given payment method.
        
        Args:
            payment_method: The payment method (e.g., 'stripe', 'razorpay', 'cod')
            request: The current request object (optional)
            
        Returns:
            PaymentGatewayService: The payment service instance
        """
        if payment_method == 'stripe':
            return StripeService(request)
        elif payment_method == 'razorpay':
            return RazorpayService(request)
        elif payment_method == 'cod':
            return CashOnDeliveryService(request)
        else:
            return None

    @staticmethod
    def get_available_services(request=None):
        """
        Get all available payment services.
        
        Args:
            request: The current request object (optional)
            
        Returns:
            dict: Dictionary of available payment services with their configuration status
        """
        services = {
            'stripe': StripeService(request),
            'razorpay': RazorpayService(request),
            'cod': CashOnDeliveryService(request),
        }

        return {
            method: {
                'service': service,
                'configured': service.is_configured(),
                'display_name': PaymentServiceFactory.get_display_name(method),
                'icon': PaymentServiceFactory.get_icon(method),
                'description': PaymentServiceFactory.get_description(method)
            }
            for method, service in services.items()
        }

    @staticmethod
    def get_display_name(payment_method):
        """
        Get the display name for a payment method.
        
        Args:
            payment_method: The payment method
            
        Returns:
            str: The display name
        """
        display_names = {
            'stripe': 'Credit/Debit Card',
            'razorpay': 'UPI/Netbanking (Razorpay)',
            'cod': 'Cash on Delivery',
        }
        return display_names.get(payment_method, payment_method.title())

    @staticmethod
    def get_icon(payment_method):
        """
        Get the icon for a payment method.
        
        Args:
            payment_method: The payment method
            
        Returns:
            str: The icon class
        """
        icons = {
            'stripe': 'far fa-credit-card',
            'razorpay': 'fas fa-money-bill-wave',
            'cod': 'fas fa-hand-holding-usd',
        }
        return icons.get(payment_method, 'fas fa-money-bill')

    @staticmethod
    def get_description(payment_method):
        """
        Get the description for a payment method.
        
        Args:
            payment_method: The payment method
            
        Returns:
            str: The description
        """
        descriptions = {
            'stripe': 'Pay securely with your credit or debit card',
            'razorpay': 'Pay using UPI, Netbanking, or Wallet',
            'cod': 'Pay with cash when your order is delivered',
        }
        return descriptions.get(payment_method, '')
