from django.db import models
from django.contrib.auth import get_user_model
from django.db import transaction
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

    @transaction.atomic
    def migrate_from_session(self, user, session_id):
        """Migrate cart from session to user when logging in."""
        try:
            session_cart = Cart.objects.select_for_update().get(session_id=session_id, user__isnull=True)

            try:
                # Try to get existing user cart
                user_cart = Cart.objects.select_for_update().get(user=user)

                # Migrate items from session cart to user cart
                for item in session_cart.items.select_for_update().all():
                    try:
                        # Check if item exists in user cart
                        user_item = user_cart.items.select_for_update().get(
                            product=item.product,
                            variant=item.variant
                        )

                        # Calculate available quantity
                        available_qty = item.variant.quantity if item.variant else item.product.quantity
                        new_quantity = min(user_item.quantity + item.quantity, available_qty)

                        # Update quantity if item already exists
                        user_item.quantity = new_quantity
                        user_item.save()
                    except CartItem.DoesNotExist:
                        # Move item to user's cart
                        item.cart = user_cart
                        item.save()

                # Delete session cart
                session_cart.delete()
                return user_cart

            except Cart.DoesNotExist:
                # Just assign the session cart to the user
                session_cart.user = user
                session_cart.session_id = None
                session_cart.save()
                return session_cart

        except Cart.DoesNotExist:
            # No session cart exists, return/create user cart
            user_cart, _ = Cart.objects.get_or_create(user=user)
            return user_cart

    def add_item(self, product, quantity=1, variant=None):
        """
        Add an item to the cart with proper validation and error handling.

        Args:
            product: The Product instance to add
            quantity: The quantity to add
            variant: Optional ProductVariant instance

        Returns:
            tuple: (success, message, cart_item)
        """
        if product.status != 'active':
            return False, "This product is not available", None

        if not product.is_in_stock:
            return False, "This product is out of stock", None

        if variant and not variant.is_in_stock:
            return False, "This variant is out of stock", None

        if product.variants.exists() and not variant:
            return False, "Please select a product variant", None

        try:
            # Check if item exists in cart
            cart_item = self.items.get(product=product, variant=variant)

            # Check available quantity
            available_qty = variant.quantity if variant else product.quantity

            if cart_item.quantity + quantity > available_qty:
                cart_item.quantity = available_qty
                cart_item.save()
                return True, f"Only {available_qty} items available. Cart updated to maximum quantity.", cart_item

            # Update quantity
            cart_item.quantity += quantity
            cart_item.save()
            return True, "Cart updated successfully", cart_item

        except CartItem.DoesNotExist:
            # Create new cart item
            available_qty = variant.quantity if variant else product.quantity
            add_quantity = min(quantity, available_qty)

            cart_item = CartItem.objects.create(
                cart=self,
                product=product,
                variant=variant,
                quantity=add_quantity
            )

            return True, "Product added to cart", cart_item


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
