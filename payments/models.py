from django.db import models
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from orders.models import Order, VendorOrder

User = get_user_model()


class PaymentMethod(models.Model):
    """Saved payment methods for users."""

    PAYMENT_TYPE_CHOICES = (
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Account'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    provider = models.CharField(max_length=50)  # Stripe, Razorpay, PayPal, etc.
    is_default = models.BooleanField(default=False)

    # Card details (if payment_type is 'card')
    card_last4 = models.CharField(max_length=4, blank=True, null=True)
    card_brand = models.CharField(max_length=20, blank=True, null=True)  # Visa, Mastercard, etc.
    card_exp_month = models.PositiveSmallIntegerField(blank=True, null=True)
    card_exp_year = models.PositiveSmallIntegerField(blank=True, null=True)

    # Bank details (if payment_type is 'bank')
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account_last4 = models.CharField(max_length=4, blank=True, null=True)

    # UPI details (if payment_type is 'upi')
    upi_id = models.CharField(max_length=100, blank=True, null=True)

    # Wallet details (if payment_type is 'wallet')
    wallet_name = models.CharField(max_length=50, blank=True, null=True)
    wallet_id = models.CharField(max_length=100, blank=True, null=True)

    # Token from payment provider for saved methods
    token = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        if self.payment_type == 'card':
            return f"{self.card_brand} ending in {self.card_last4}"
        elif self.payment_type == 'bank':
            return f"{self.bank_name} account ending in {self.bank_account_last4}"
        elif self.payment_type == 'upi':
            return f"UPI: {self.upi_id}"
        elif self.payment_type == 'wallet':
            return f"{self.wallet_name}: {self.wallet_id}"
        return f"Payment method ({self.id})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other payment methods of this user to not default
            PaymentMethod.objects.filter(
                user=self.user,
                payment_type=self.payment_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Transaction(models.Model):
    """Record of all payment transactions."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
        ('expired', 'Expired'),
    )

    TRANSACTION_TYPE_CHOICES = (
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('payout', 'Vendor Payout'),
    )

    transaction_id = models.CharField(max_length=100, unique=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    payment_method = models.CharField(max_length=50)  # Credit card, UPI, wallet, etc.
    provider = models.CharField(max_length=50)  # Stripe, Razorpay, PayPal, etc.
    provider_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)  # Additional transaction details
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type.capitalize()} - {self.amount} {self.currency} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate a unique transaction ID
            self.transaction_id = f"TXN-{get_random_string(length=12, allowed_chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')}"
        super().save(*args, **kwargs)


class VendorPayout(models.Model):
    """Payouts to vendors for their sales."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    vendor_order = models.ForeignKey(VendorOrder, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendor_payout'
    )
    payout_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payout to {self.vendor_order.vendor.business_name} - {self.amount}"
