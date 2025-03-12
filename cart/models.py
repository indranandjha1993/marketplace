from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant

User = get_user_model()


class Cart(models.Model):
    """Shopping cart for users."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)  # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                        models.Q(user__isnull=False) |
                        models.Q(session_id__isnull=False)
                ),
                name='cart_user_or_session'
            )
        ]

    def __str__(self):
        if self.user:
            return f"Cart - {self.user.email}"
        return f"Cart - {self.session_id}"

    @property
    def total_items(self):
        """Return the total number of items in the cart."""
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        """Return the subtotal of all items in the cart."""
        return sum(item.subtotal for item in self.items.all())

    @property
    def tax_amount(self):
        """Return the total tax amount for all items in the cart."""
        return sum(item.tax_amount for item in self.items.all())

    @property
    def total(self):
        """Return the total cost of all items in the cart."""
        return self.subtotal + self.tax_amount

    def clear(self):
        """Remove all items from the cart."""
        self.items.all().delete()

    def migrate_from_session(self, user, session_id):
        """Migrate cart from session to user when logging in."""
        try:
            session_cart = Cart.objects.get(session_id=session_id, user__isnull=True)
            try:
                user_cart = Cart.objects.get(user=user)
                # Migrate items from session cart to user cart
                for item in session_cart.items.all():
                    try:
                        user_item = user_cart.items.get(
                            product=item.product,
                            variant=item.variant
                        )
                        # Update quantity if item already exists
                        user_item.quantity += item.quantity
                        user_item.save()
                    except CartItem.DoesNotExist:
                        # Move item to user's cart
                        item.cart = user_cart
                        item.save()
                # Delete session cart
                session_cart.delete()
            except Cart.DoesNotExist:
                # Just assign the session cart to the user
                session_cart.user = user
                session_cart.session_id = None
                session_cart.save()
        except Cart.DoesNotExist:
            pass


class CartItem(models.Model):
    """Individual items in a shopping cart."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product', 'variant')

    def __str__(self):
        product_name = self.product.title
        if self.variant:
            variant_name = ', '.join(
                [f"{val.attribute.name}: {val.value}" for val in self.variant.attribute_values.all()])
            return f"{self.quantity} x {product_name} ({variant_name})"
        return f"{self.quantity} x {product_name}"

    @property
    def unit_price(self):
        """Return the unit price of the item."""
        if self.variant:
            return self.variant.price
        return self.product.current_price

    @property
    def subtotal(self):
        """Return the subtotal for this item."""
        return self.unit_price * self.quantity

    @property
    def tax_rate(self):
        """Return the tax rate for this item."""
        return self.product.tax_rate

    @property
    def tax_amount(self):
        """Return the tax amount for this item."""
        return round(self.subtotal * (self.tax_rate / 100), 2)

    @property
    def total(self):
        """Return the total for this item including tax."""
        return self.subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        # Ensure quantity doesn't exceed available stock
        if self.variant:
            available = self.variant.quantity
        else:
            available = self.product.quantity

        if self.quantity > available:
            self.quantity = available

        super().save(*args, **kwargs)


class SavedForLater(models.Model):
    """Items saved for later from cart."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product', 'variant')

    def __str__(self):
        product_name = self.product.title
        if self.variant:
            variant_name = ', '.join(
                [f"{val.attribute.name}: {val.value}" for val in self.variant.attribute_values.all()])
            return f"Saved - {product_name} ({variant_name})"
        return f"Saved - {product_name}"
