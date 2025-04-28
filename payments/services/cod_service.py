from .base import PaymentGatewayService


class CashOnDeliveryService(PaymentGatewayService):
    """
    Cash on Delivery payment service implementation.
    """

    def _initialize(self):
        """
        Initialize the COD service.
        """
        # No initialization needed for COD
        pass

    def is_configured(self):
        """
        Check if COD is properly configured.
        
        Returns:
            bool: Always True for COD
        """
        return True

    def create_payment(self, order, **kwargs):
        """
        Create a COD payment for the given order.
        
        Args:
            order: The order to create a payment for
            **kwargs: Additional arguments
            
        Returns:
            dict: Payment creation response
        """
        return {
            'success': True,
            'payment_method': 'cod',
            'status': 'pending',
            'message': 'Order placed successfully. Payment will be collected on delivery.'
        }

    def verify_payment(self, order, **kwargs):
        """
        Verify a COD payment for the given order.
        
        Args:
            order: The order to verify payment for
            **kwargs: Additional arguments
            
        Returns:
            dict: Payment verification response
        """
        return {
            'success': True,
            'verified': True,
            'payment_method': 'cod',
            'status': 'pending',
            'message': 'Payment will be collected on delivery.'
        }
