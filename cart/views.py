from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db import transaction

from products.models import Product, ProductVariant
from orders.models import ShippingMethod
from .models import Cart, CartItem, SavedForLater


def get_or_create_cart(request):
    """
    Helper function to get or create a cart for the current user/session.
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key

        cart, _ = Cart.objects.get_or_create(session_id=session_id, user__isnull=True)

    return cart


def cart_detail(request):
    """
    View for displaying cart details with enhanced features.
    """
    cart = get_or_create_cart(request)

    # Check for saved items
    saved_items = []
    if request.user.is_authenticated:
        saved_items = SavedForLater.objects.filter(user=request.user)
        
    # Get cart items with all related data for better performance
    cart_items = cart.items.select_related(
        'product', 
        'variant', 
        'product__vendor'
    ).prefetch_related(
        'variant__attribute_values',
        'variant__attribute_values__attribute'
    ).all()
    
    # Check for items with price changes
    price_changed_items = [item for item in cart_items if item.has_price_changed]
    
    # Check for out of stock items
    out_of_stock_items = [item for item in cart_items if not item.is_in_stock]
    
    # Get available shipping methods
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    
    # Get the selected shipping method or use the default
    selected_shipping_method = cart.shipping_method
    
    # If no shipping method is selected, use the first available one
    if not selected_shipping_method and shipping_methods.exists() and cart.has_physical_items:
        selected_shipping_method = shipping_methods.first()
        cart.shipping_method = selected_shipping_method
    
    # Calculate shipping cost based on selected method
    shipping_cost = 0
    if cart.has_physical_items and selected_shipping_method:
        shipping_cost = selected_shipping_method.get_price_for_cart(cart)
    
    # Set shipping cost on cart object
    cart.shipping_cost = shipping_cost
    cart.save()
    
    # Get estimated delivery dates
    estimated_delivery = cart.estimated_delivery

    # Check if a coupon is applied in the session
    coupon_id = request.session.get('coupon_id')
    coupon = None
    coupon_discount = 0

    if coupon_id:
        from orders.models import Coupon
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid:
                coupon_discount = coupon.calculate_discount(cart.subtotal)
            else:
                # Remove invalid coupon
                del request.session['coupon_id']
                messages.warning(request, 'The coupon has expired or is no longer valid')
        except Coupon.DoesNotExist:
            if 'coupon_id' in request.session:
                del request.session['coupon_id']
    
    # Calculate final total
    final_total = cart.total - coupon_discount
    
    # Check for recently viewed products
    recently_viewed = []
    if 'recently_viewed' in request.session:
        from products.models import Product
        product_ids = request.session['recently_viewed'][:4]  # Get last 4 viewed products
        recently_viewed = Product.objects.filter(id__in=product_ids, status='active')

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'saved_items': saved_items,
        'coupon': coupon,
        'coupon_discount': coupon_discount,
        'final_total': final_total,
        'shipping_cost': shipping_cost,
        'shipping_methods': shipping_methods,
        'selected_shipping_method': selected_shipping_method,
        'price_changed_items': price_changed_items,
        'out_of_stock_items': out_of_stock_items,
        'estimated_delivery': estimated_delivery,
        'recently_viewed': recently_viewed,
        'has_digital_items': cart.has_digital_items,
        'has_physical_items': cart.has_physical_items
    }

    return render(request, 'cart/cart_detail.html', context)


@require_POST
def add_to_cart(request, product_id):
    """
    View for adding a product to the cart with enhanced features.
    """
    try:
        with transaction.atomic():
            # Get the product with select_related for better performance
            product = get_object_or_404(
                Product.objects.select_related('vendor'), 
                id=product_id, 
                status='active'
            )

            cart = get_or_create_cart(request)

            # Parse quantity with validation
            try:
                quantity = int(request.POST.get('quantity', 1))
                if quantity <= 0:
                    raise ValueError("Quantity must be greater than zero")
            except ValueError:
                messages.error(request, 'Please provide a valid quantity')
                return redirect('products:product_detail', product_slug=product.slug)

            # Get variant if specified
            variant_id = request.POST.get('variant_id')
            variant = None

            # Check if product has variants
            has_variants = product.variants.exists()

            # Handle variant selection
            if has_variants:
                # If variant ID is not provided or empty
                if not variant_id or variant_id.strip() == '':
                    messages.info(request, 'Please select a product variant')
                    return redirect('products:product_detail', product_slug=product.slug)

                try:
                    # Get the selected variant with prefetch_related for better performance
                    variant = ProductVariant.objects.prefetch_related(
                        'attribute_values', 
                        'attribute_values__attribute'
                    ).get(id=variant_id, product=product)

                except ProductVariant.DoesNotExist:
                    messages.error(request, 'Selected variant not found')
                    return redirect('products:product_detail', product_slug=product.slug)

            # Get optional parameters
            item_note = request.POST.get('item_note', None)
            is_gift = request.POST.get('is_gift', False) == 'true'
            gift_message = request.POST.get('gift_message', None) if is_gift else None
            
            # Check if return path is provided
            next_url = request.POST.get('next', '')

            # Use the enhanced add_item method
            success, message, cart_item = cart.add_item(
                product=product,
                quantity=quantity,
                variant=variant,
                item_note=item_note,
                is_gift=is_gift,
                gift_message=gift_message
            )

            if success:
                # Format product name with variant details for the message
                product_name = product.title
                if variant:
                    variant_details = ', '.join([f"{val.attribute.name}: {val.value}"
                                               for val in variant.attribute_values.all()])
                    product_name = f"{product.title} ({variant_details})"
                
                # Add success message with product details
                if "maximum quantity" in message:
                    messages.warning(request, message)
                else:
                    messages.success(request, f'{product_name} added to cart')
                    
                # Track recently viewed products
                if 'recently_viewed' not in request.session:
                    request.session['recently_viewed'] = []
                
                # Add to recently viewed and ensure product_id is at the front of the list
                recently_viewed = request.session['recently_viewed']
                if product_id in recently_viewed:
                    recently_viewed.remove(product_id)
                recently_viewed.insert(0, product_id)
                # Keep only the last 10 viewed products
                request.session['recently_viewed'] = recently_viewed[:10]
                request.session.modified = True
            else:
                messages.error(request, message)
                
            # Redirect to the provided URL or cart detail page
            if next_url:
                return redirect(next_url)
            return redirect('cart:cart_detail')

    except Exception as e:
        messages.error(request, f'Error adding to cart: {str(e)}')
        return redirect('products:product_detail', product_slug=product.slug)


@require_POST
def update_cart(request, item_id):
    """
    View for updating the quantity of an item in the cart with enhanced features.
    """
    cart = get_or_create_cart(request)
    next_url = request.POST.get('next', 'cart:cart_detail')

    try:
        cart_item = CartItem.objects.select_related('product', 'variant').get(id=item_id, cart=cart)

        # Get quantity and validate
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            messages.error(request, 'Invalid quantity')
            return redirect(next_url)
            
        # Get optional parameters
        item_note = request.POST.get('item_note')
        is_gift = request.POST.get('is_gift') == 'on'
        gift_message = request.POST.get('gift_message')
        
        # Update optional fields if provided
        if item_note is not None:
            cart_item.item_note = item_note
            
        if 'is_gift' in request.POST:
            cart_item.is_gift = is_gift
            if is_gift and gift_message:
                cart_item.gift_message = gift_message
            elif not is_gift:
                cart_item.gift_message = None
        
        # Use the enhanced update_quantity method
        success, message = cart_item.update_quantity(quantity)
        
        if success:
            if "maximum quantity" in message:
                messages.warning(request, message)
            else:
                messages.success(request, message)
        else:
            messages.info(request, message)

    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found in cart')

    return redirect(next_url)


@require_POST
def remove_from_cart(request, item_id):
    """
    View for removing an item from the cart.
    """
    cart = get_or_create_cart(request)
    next_url = request.POST.get('next', 'cart:cart_detail')

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        messages.success(request, 'Item removed from cart')
    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found in cart')

    return redirect(next_url)


@require_POST
def clear_cart(request):
    """
    View for clearing all items from the cart.
    """
    cart = get_or_create_cart(request)
    cart.clear()

    # Remove coupon if applied
    if 'coupon_id' in request.session:
        del request.session['coupon_id']

    messages.success(request, 'Cart cleared successfully')
    return redirect('cart:cart_detail')


@login_required
@require_POST
def save_for_later(request, item_id):
    """
    View for moving an item from the cart to the saved items list with enhanced features.
    """
    cart = get_or_create_cart(request)
    next_url = request.POST.get('next', 'cart:cart_detail')

    try:
        cart_item = CartItem.objects.select_related('product', 'variant').get(id=item_id, cart=cart)
        
        # Get the current price for tracking price changes
        current_price = cart_item.unit_price
        
        # Get optional note
        note = request.POST.get('note') or cart_item.item_note

        # Check if the item already exists in saved items
        try:
            # Try to get existing saved item
            saved_item = SavedForLater.objects.get(
                user=request.user,
                product=cart_item.product,
                variant=cart_item.variant
            )
            # Update the note if provided
            if note:
                saved_item.note = note
                saved_item.save()
                
            messages.info(request, 'This item was already in your saved items')
            
        except SavedForLater.DoesNotExist:
            # Create new saved item
            SavedForLater.objects.create(
                user=request.user,
                product=cart_item.product,
                variant=cart_item.variant,
                price_at_save=current_price,
                note=note
            )
            messages.success(request, 'Item saved for later')

        # Remove from cart
        cart_item.delete()

    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found in cart')

    return redirect(next_url)


@login_required
@require_POST
def move_to_cart(request, item_id):
    """
    View for moving an item from the saved items list to the cart with enhanced features.
    """
    next_url = request.POST.get('next', 'cart:cart_detail')

    try:
        saved_item = SavedForLater.objects.select_related('product', 'variant').get(id=item_id, user=request.user)
        cart = get_or_create_cart(request)

        # Check if the product is still active and in stock
        product = saved_item.product
        if product.status != 'active':
            messages.error(request, 'This product is no longer available')
            saved_item.delete()  # Remove unavailable product from saved items
            return redirect(next_url)

        if not product.is_in_stock:
            messages.error(request, 'This product is out of stock')
            return redirect(next_url)

        # If it's a variant, check variant status
        if saved_item.variant and not saved_item.variant.is_in_stock:
            messages.error(request, 'This product variant is out of stock')
            return redirect(next_url)

        # Get quantity from form or default to 1
        try:
            quantity = int(request.POST.get('quantity', 1))
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero")
        except ValueError:
            quantity = 1
            
        # Get optional parameters
        item_note = saved_item.note
        is_gift = request.POST.get('is_gift', False) == 'on'
        gift_message = request.POST.get('gift_message', None) if is_gift else None

        # Use the enhanced add_item method
        success, message, cart_item = cart.add_item(
            product=product,
            quantity=quantity,
            variant=saved_item.variant,
            item_note=item_note,
            is_gift=is_gift,
            gift_message=gift_message
        )

        if success:
            # Remove from saved items
            saved_item.delete()
            
            # Format product name with variant details for the message
            product_name = product.title
            if saved_item.variant:
                variant_details = ', '.join([f"{val.attribute.name}: {val.value}"
                                           for val in saved_item.variant.attribute_values.all()])
                product_name = f"{product.title} ({variant_details})"
            
            # Check if price has changed since item was saved
            if saved_item.has_price_changed:
                if saved_item.price_change_amount > 0:
                    messages.info(request, 
                        f'Note: The price of this item has increased by {saved_item.price_change_percentage}% since you saved it')
                else:
                    messages.info(request, 
                        f'Good news! The price of this item has decreased by {abs(saved_item.price_change_percentage)}% since you saved it')
            
            messages.success(request, f'{product_name} moved to cart')
        else:
            messages.error(request, message)

    except SavedForLater.DoesNotExist:
        messages.error(request, 'Saved item not found')

    return redirect(next_url)


@login_required
@require_POST
def remove_from_saved(request, item_id):
    """
    View for removing an item from the saved items list.
    """
    next_url = request.POST.get('next', 'cart:cart_detail')

    try:
        saved_item = SavedForLater.objects.get(id=item_id, user=request.user)
        saved_item.delete()
        messages.success(request, 'Item removed from saved items')
    except SavedForLater.DoesNotExist:
        messages.error(request, 'Saved item not found')

    return redirect(next_url)


@login_required
@require_POST
def move_all_to_cart(request):
    """
    View for moving all items from the saved items list to the cart.
    """
    next_url = request.POST.get('next', 'cart:cart_detail')

    # Get all saved items for the user
    saved_items = SavedForLater.objects.filter(user=request.user)

    if not saved_items.exists():
        messages.info(request, 'You have no saved items to move to cart')
        return redirect(next_url)

    cart = get_or_create_cart(request)
    success_count = 0
    error_count = 0

    for saved_item in saved_items:
        product = saved_item.product

        # Skip unavailable products
        if product.status != 'active':
            saved_item.delete()  # Remove unavailable product from saved items
            error_count += 1
            continue

        # Skip out of stock products
        if not product.is_in_stock:
            error_count += 1
            continue

        # If it's a variant, check variant status
        if saved_item.variant and not saved_item.variant.is_in_stock:
            error_count += 1
            continue

        # Check if the item already exists in the cart
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product=product,
                variant=saved_item.variant
            )

            # Check available quantity before updating
            available_qty = saved_item.variant.quantity if saved_item.variant else product.quantity

            if cart_item.quantity + 1 > available_qty:
                error_count += 1
                continue
            else:
                cart_item.quantity += 1
                cart_item.save()
                saved_item.delete()
                success_count += 1

        except CartItem.DoesNotExist:
            # Create new cart item with quantity 1
            CartItem.objects.create(
                cart=cart,
                product=product,
                variant=saved_item.variant,
                quantity=1
            )

            # Remove from saved items
            saved_item.delete()
            success_count += 1

    # Display appropriate messages based on the results
    if success_count > 0:
        messages.success(request, f'{success_count} item(s) moved to cart successfully')

    if error_count > 0:
        messages.warning(request, f'{error_count} item(s) could not be moved to cart due to availability issues')

    return redirect(next_url)


@login_required
@require_POST
def clear_saved_items(request):
    """
    View for removing all items from the saved items list.
    """
    next_url = request.POST.get('next', 'cart:cart_detail')

    # Get all saved items for the user
    saved_items = SavedForLater.objects.filter(user=request.user)

    if not saved_items.exists():
        messages.info(request, 'You have no saved items to clear')
        return redirect(next_url)

    # Count items before deletion for the message
    item_count = saved_items.count()

    # Delete all saved items
    saved_items.delete()

    messages.success(request, f'All {item_count} saved item(s) have been removed')
    return redirect(next_url)


@require_POST
def apply_coupon(request):
    """
    View for applying a coupon to the cart.
    """
    coupon_code = request.POST.get('coupon_code')

    if not coupon_code:
        messages.error(request, 'Please enter a coupon code')
        return redirect('cart:cart_detail')

    try:
        from orders.models import Coupon
        coupon = Coupon.objects.get(code__iexact=coupon_code, is_active=True)

        # Check if coupon is valid
        if not coupon.is_valid:
            messages.error(request, 'This coupon has expired or is no longer valid')
            return redirect('cart:cart_detail')

        # Check if the user has already used this coupon
        if request.user.is_authenticated:
            user_coupon_usage = coupon.orders.filter(user=request.user).count()
            if user_coupon_usage >= coupon.max_usage_per_user:
                messages.error(request, 'You have already used this coupon the maximum number of times')
                return redirect('cart:cart_detail')

        # Check minimum order amount
        cart = get_or_create_cart(request)
        if cart.subtotal < coupon.minimum_order_amount:
            messages.error(request, f'This coupon requires a minimum order amount of ₹{coupon.minimum_order_amount}')
            return redirect('cart:cart_detail')

        # Store coupon in session
        request.session['coupon_id'] = coupon.id
        messages.success(request, 'Coupon applied successfully')

    except Coupon.DoesNotExist:
        messages.error(request, 'Invalid coupon code')

    return redirect('cart:cart_detail')


@require_POST
def remove_coupon(request):
    """
    View for removing a coupon from the cart.
    """
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        messages.success(request, 'Coupon removed successfully')

    return redirect('cart:cart_detail')


@require_POST
def update_shipping_method(request):
    """Update the shipping method for the cart."""
    shipping_method_id = request.POST.get('shipping_method_id')
    
    if not shipping_method_id:
        messages.error(request, "No shipping method selected.")
        return redirect('cart:cart_detail')
    
    try:
        shipping_method = ShippingMethod.objects.get(id=shipping_method_id, is_active=True)
        cart = get_or_create_cart(request)
        
        # Update shipping method
        cart.shipping_method = shipping_method
        
        # Calculate shipping cost
        if cart.has_physical_items:
            cart.shipping_cost = shipping_method.get_price_for_cart(cart)
        else:
            cart.shipping_cost = 0
            
        cart.save()
        messages.success(request, f"Shipping method updated to {shipping_method.name}.")
        
    except ShippingMethod.DoesNotExist:
        messages.error(request, "Invalid shipping method selected.")
    
    return redirect('cart:cart_detail')
