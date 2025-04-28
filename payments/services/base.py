from abc import ABC, abstractmethod

from django.urls import reverse


class PaymentGatewayService(ABC):
    """
    Abstract base class for payment gateway services.
    All payment gateway implementations should inherit from this class.
    """

    def __init__(self, request=None):
        """
        Initialize the payment gateway service.
        
        Args:
            request: The current request object (optional)
        """
        self.request = request
        self._initialize()

    @abstractmethod
    def _initialize(self):
        """
        Initialize the payment gateway client.
        This method should be implemented by subclasses.
        """
        pass

    @abstractmethod
    def is_configured(self):
        """
        Check if the payment gateway is properly configured.
        
        Returns:
            bool: True if the gateway is configured, False otherwise
        """
        pass

    @abstractmethod
    def create_payment(self, order, **kwargs):
        """
        Create a payment for the given order.
        
        Args:
            order: The order to create a payment for
            **kwargs: Additional arguments specific to the payment gateway
            
        Returns:
            dict: Payment creation response with relevant data
        """
        pass

    @abstractmethod
    def verify_payment(self, order, **kwargs):
        """
        Verify a payment for the given order.
        
        Args:
            order: The order to verify payment for
            **kwargs: Additional arguments specific to the payment gateway
            
        Returns:
            dict: Payment verification response with status and data
        """
        pass

    def get_success_url(self, order_number):
        """
        Get the success URL for the payment.
        
        Args:
            order_number: The order number
            
        Returns:
            str: The absolute URL for success
        """
        if self.request:
            return self.request.build_absolute_uri(
                reverse('payments:verify_payment', args=[order_number])
            )
        return reverse('payments:verify_payment', args=[order_number])

    def get_cancel_url(self, order_number):
        """
        Get the cancel URL for the payment.
        
        Args:
            order_number: The order number
            
        Returns:
            str: The absolute URL for cancellation
        """
        if self.request:
            return self.request.build_absolute_uri(
                reverse('payments:payment_failed', args=[order_number])
            )
        return reverse('payments:payment_failed', args=[order_number])

    def get_callback_url(self, order_number):
        """
        Get the callback URL for the payment.
        
        Args:
            order_number: The order number
            
        Returns:
            str: The absolute URL for callback
        """
        if self.request:
            return self.request.build_absolute_uri(
                reverse('payments:verify_payment', args=[order_number])
            )
        return reverse('payments:verify_payment', args=[order_number])
