from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant
from accounts.models import UserAddress
from vendors.models import Vendor

User = get_user_model()


class Order(models.Model):
    """Main order model for customer purchases."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True)
    shipping_address = models.ForeignKey(
        UserAddress,
        on_delete=models.SET_NULL,
        related_name='shipping_orders',
        null=True
    )
    billing_address = models.ForeignKey(
        UserAddress,
        on_delete=models.SET_NULL,
        related_name='billing_orders',
        null=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        related_name='orders',
        blank=True,
        null=True
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def get_vendor_orders(self):
        """Return all VendorOrder instances for this order."""
        return self.vendor_orders.all()

    def get_total_items(self):
        """Return total number of items in the order."""
        return sum(item.quantity for item in self.items.all())


class VendorOrder(models.Model):
    """Order details specific to each vendor."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='vendor_orders')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_vendor_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tracking_number = models.CharField(max_length=255, blank=True, null=True)
    carrier = models.CharField(max_length=100, blank=True, null=True)
    dispatch_date = models.DateTimeField(blank=True, null=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('order', 'vendor')

    def __str__(self):
        return f"Vendor Order: {self.vendor.business_name} - Order #{self.order.order_number}"

    def get_vendor_items(self):
        """Return only the items from this vendor."""
        return self.order.items.filter(product__vendor=self.vendor)


class OrderItem(models.Model):
    """Individual items in an order."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        related_name='order_items',
        blank=True,
        null=True
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def save(self, *args, **kwargs):
        # Calculate total if not provided
        if not self.total:
            self.total = (self.price * self.quantity) - self.discount_amount + self.tax_amount
        super().save(*args, **kwargs)


class Payment(models.Model):
    """Payment information for orders."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider = models.CharField(max_length=50)  # Stripe, Razorpay, PayPal, etc.
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    transaction_id = models.CharField(max_length=255)
    payment_method = models.CharField(max_length=50)  # Credit card, UPI, wallet, etc.
    payment_data = models.JSONField(blank=True, null=True)  # Additional payment details
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment: {self.amount} - Order #{self.order.order_number}"


class Refund(models.Model):
    """Refund information for orders."""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    refund_data = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund: {self.amount} - Order #{self.order.order_number}"


class OrderTracking(models.Model):
    """History of order status changes."""
    STATUS_CHOICES = (
        ('pending', 'Order Received'),
        ('confirmed', 'Order Confirmed'),
        ('processing', 'Processing'),
        ('packed', 'Packed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
    )

    vendor_order = models.ForeignKey(VendorOrder, on_delete=models.CASCADE, related_name='tracking_history')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Order #{self.vendor_order.order.order_number} - {self.status} ({self.timestamp})"


class Coupon(models.Model):
    """Discount coupons that can be applied to orders."""

    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_usage = models.IntegerField(default=1)  # Total number of times the coupon can be used
    max_usage_per_user = models.IntegerField(default=1)  # Number of times a user can use the coupon
    usage_count = models.IntegerField(default=0)  # Current usage count

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        """Check if the coupon is currently valid."""
        from django.utils import timezone
        now = timezone.now()
        return (
                self.is_active and
                self.valid_from <= now <= self.valid_to and
                self.usage_count < self.max_usage
        )

    def calculate_discount(self, amount):
        """Calculate the discount for a given amount."""
        if not self.is_valid:
            return 0

        if amount < self.minimum_order_amount:
            return 0

        if self.discount_type == 'percentage':
            return round(amount * (self.discount_value / 100), 2)
        else:  # fixed amount
            return min(self.discount_value, amount)  # Don't discount more than the order amount
