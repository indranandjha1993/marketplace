from django.db import models
from django.contrib.auth import get_user_model
from django.db import transaction
from products.models import Product, ProductVariant
from orders.models import ShippingMethod

User = get_user_model()


class Cart(models.Model):
    """Shopping cart for users."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)  # For anonymous users
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True, help_text="Last time the cart was modified")
    shipping_method = models.ForeignKey(
        ShippingMethod, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='carts',
        help_text="Selected shipping method"
    )
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, null=True, help_text="Customer notes for the order")

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
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        if self.user:
            return f"Cart - {self.user.email}"
        return f"Cart - {self.session_id}"

    @property
    def total_items(self):
        """Return the total number of items in the cart."""
        # Use annotation for better performance
        from django.db.models import Sum
        result = self.items.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    @property
    def total_unique_items(self):
        """Return the number of unique items in the cart."""
        return self.items.count()

    @property
    def subtotal(self):
        """Return the subtotal of all items in the cart."""
        return sum(item.subtotal for item in self.items.select_related('product', 'variant').all())

    @property
    def tax_amount(self):
        """Return the total tax amount for all items in the cart."""
        return sum(item.tax_amount for item in self.items.select_related('product').all())

    @property
    def total(self):
        """Return the total cost of all items in the cart including shipping."""
        return self.subtotal + self.tax_amount + self.shipping_cost

    @property
    def has_digital_items(self):
        """Check if cart contains any digital items."""
        # Use a more explicit approach to avoid the lookup error
        for item in self.items.select_related('product').all():
            if hasattr(item.product, 'is_digital') and item.product.is_digital:
                return True
        return False
    
    @property
    def has_physical_items(self):
        """Check if cart contains any physical items."""
        # Use a more explicit approach to avoid the lookup error
        for item in self.items.select_related('product').all():
            if hasattr(item.product, 'is_digital') and not item.product.is_digital:
                return True
        return False
    
    @property
    def estimated_delivery(self):
        """Return the estimated delivery date range."""
        import datetime
        from django.utils import timezone
        
        if not self.has_physical_items:
            return None
            
        # Get the longest delivery time from all items
        max_days = 3  # Default delivery time
        for item in self.items.select_related('product').all():
            # Check if product has the is_digital attribute and it's not a digital product
            if (hasattr(item.product, 'is_digital') and not item.product.is_digital and 
                hasattr(item.product, 'delivery_days') and item.product.delivery_days > max_days):
                max_days = item.product.delivery_days
                
        min_date = timezone.now().date() + datetime.timedelta(days=2)
        max_date = timezone.now().date() + datetime.timedelta(days=max_days)
        
        return {
            'min_date': min_date,
            'max_date': max_date
        }

    def clear(self):
        """Remove all items from the cart."""
        self.items.all().delete()
        
    def is_empty(self):
        """Check if the cart is empty."""
        return self.total_items == 0

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

    def add_item(self, product, quantity=1, variant=None, item_note=None, is_gift=False, gift_message=None):
        """
        Add an item to the cart with proper validation and error handling.

        Args:
            product: The Product instance to add
            quantity: The quantity to add
            variant: Optional ProductVariant instance
            item_note: Optional note for the item
            is_gift: Whether this item is a gift
            gift_message: Optional gift message if is_gift is True

        Returns:
            tuple: (success, message, cart_item)
        """
        # Validate product status
        if product.status != 'active':
            return False, "This product is not available", None

        # Check if product is in stock
        if not product.is_in_stock:
            return False, "This product is out of stock", None

        # Check variant stock if applicable
        if variant and not variant.is_in_stock:
            return False, "This variant is out of stock", None

        # Ensure variant is selected if product has variants
        if product.variants.exists() and not variant:
            return False, "Please select a product variant", None

        # Validate quantity
        if quantity <= 0:
            return False, "Quantity must be greater than zero", None

        try:
            # Check if item exists in cart
            cart_item = self.items.get(product=product, variant=variant)

            # Check available quantity
            available_qty = variant.quantity if variant else product.quantity

            if cart_item.quantity + quantity > available_qty:
                cart_item.quantity = available_qty
                cart_item.save()
                return True, f"Only {available_qty} items available. Cart updated to maximum quantity.", cart_item

            # Update quantity and other fields if provided
            cart_item.quantity += quantity
            
            # Update optional fields if provided
            if item_note is not None:
                cart_item.item_note = item_note
                
            if is_gift:
                cart_item.is_gift = True
                if gift_message is not None:
                    cart_item.gift_message = gift_message
                    
            cart_item.save()
            return True, "Cart updated successfully", cart_item

        except CartItem.DoesNotExist:
            # Calculate available quantity
            available_qty = variant.quantity if variant else product.quantity
            add_quantity = min(quantity, available_qty)

            # Get current price for tracking price changes
            current_price = variant.current_price if variant else product.current_price

            # Create new cart item
            cart_item = CartItem.objects.create(
                cart=self,
                product=product,
                variant=variant,
                quantity=add_quantity,
                item_note=item_note,
                is_gift=is_gift,
                gift_message=gift_message if is_gift else None,
                price_at_addition=current_price
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
    item_note = models.CharField(max_length=255, blank=True, null=True, help_text="Customer note for this item")
    is_gift = models.BooleanField(default=False, help_text="Whether this item is a gift")
    gift_message = models.TextField(blank=True, null=True, help_text="Gift message if this item is a gift")
    price_at_addition = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                           help_text="Price when item was added to cart")

    class Meta:
        unique_together = ('cart', 'product', 'variant')
        indexes = [
            models.Index(fields=['cart', 'product']),
            models.Index(fields=['added_at']),
        ]
        ordering = ['-added_at']

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
            return self.variant.current_price
        return self.product.current_price

    @property
    def original_price(self):
        """Return the original price before any discounts."""
        if self.variant:
            return self.variant.price
        return self.product.price

    @property
    def discount_amount(self):
        """Return the discount amount per unit."""
        return self.original_price - self.unit_price

    @property
    def discount_percentage(self):
        """Return the discount percentage."""
        if self.original_price > 0:
            return round((self.discount_amount / self.original_price) * 100)
        return 0

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
        
    @property
    def is_in_stock(self):
        """Check if the item is still in stock with the current quantity."""
        available = self.variant.quantity if self.variant else self.product.quantity
        return available >= self.quantity
        
    @property
    def available_quantity(self):
        """Return the available quantity for this product/variant."""
        return self.variant.quantity if self.variant else self.product.quantity
        
    @property
    def has_price_changed(self):
        """Check if the price has changed since the item was added to cart."""
        if not self.price_at_addition:
            return False
        current_price = self.unit_price
        return abs(current_price - self.price_at_addition) > 0.01
        
    @property
    def price_change_amount(self):
        """Return the amount by which the price has changed."""
        if not self.price_at_addition:
            return 0
        return self.unit_price - self.price_at_addition

    def save(self, *args, **kwargs):
        # Ensure quantity doesn't exceed available stock
        if self.variant:
            available = self.variant.quantity
        else:
            available = self.product.quantity

        if self.quantity > available:
            self.quantity = available
            
        # Store the current price when first adding the item
        if not self.pk and not self.price_at_addition:
            self.price_at_addition = self.unit_price

        super().save(*args, **kwargs)
        
    def update_quantity(self, new_quantity):
        """Update quantity with validation."""
        if new_quantity <= 0:
            self.delete()
            return False, "Item removed from cart"
            
        available = self.variant.quantity if self.variant else self.product.quantity
        
        if new_quantity > available:
            self.quantity = available
            self.save()
            return True, f"Only {available} items available. Updated to maximum quantity."
            
        self.quantity = new_quantity
        self.save()
        return True, "Quantity updated successfully"


class SavedForLater(models.Model):
    """Items saved for later from cart."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    price_at_save = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                       help_text="Price when item was saved for later")
    note = models.CharField(max_length=255, blank=True, null=True, help_text="Note for this saved item")

    class Meta:
        unique_together = ('user', 'product', 'variant')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['added_at']),
        ]
        ordering = ['-added_at']

    def __str__(self):
        product_name = self.product.title
        if self.variant:
            variant_name = ', '.join(
                [f"{val.attribute.name}: {val.value}" for val in self.variant.attribute_values.all()])
            return f"Saved - {product_name} ({variant_name})"
        return f"Saved - {product_name}"
        
    @property
    def current_price(self):
        """Return the current price of the item."""
        if self.variant:
            return self.variant.current_price
        return self.product.current_price
        
    @property
    def is_in_stock(self):
        """Check if the item is still in stock."""
        if self.variant:
            return self.variant.is_in_stock
        return self.product.is_in_stock
        
    @property
    def has_price_changed(self):
        """Check if the price has changed since the item was saved."""
        if not self.price_at_save:
            return False
        return abs(self.current_price - self.price_at_save) > 0.01
        
    @property
    def price_change_amount(self):
        """Return the amount by which the price has changed."""
        if not self.price_at_save:
            return 0
        return self.current_price - self.price_at_save
        
    @property
    def price_change_percentage(self):
        """Return the percentage by which the price has changed."""
        if not self.price_at_save or self.price_at_save == 0:
            return 0
        return round((self.price_change_amount / self.price_at_save) * 100, 1)
        
    def save(self, *args, **kwargs):
        # Store the current price when first saving the item
        if not self.pk and not self.price_at_save:
            if self.variant:
                self.price_at_save = self.variant.current_price
            else:
                self.price_at_save = self.product.current_price
                
        super().save(*args, **kwargs)