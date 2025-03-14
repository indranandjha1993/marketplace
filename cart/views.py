from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from orders.models import Coupon
from products.models import Product, ProductVariant
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

        cart, created = Cart.objects.get_or_create(session_id=session_id)

    return cart


def cart_detail(request):
    """
    View for displaying cart details.
    """
    cart = get_or_create_cart(request)

    # Check for saved items
    saved_items = []
    if request.user.is_authenticated:
        saved_items = SavedForLater.objects.filter(user=request.user)

    # Check if a coupon is applied in the session
    coupon_id = request.session.get('coupon_id')
    coupon = None
    coupon_discount = 0

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid:
                coupon_discount = coupon.calculate_discount(cart.subtotal)
            else:
                # Remove invalid coupon
                del request.session['coupon_id']
                messages.warning(request, 'The coupon has expired or is no longer valid')
        except Coupon.DoesNotExist:
            del request.session['coupon_id']

    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('product', 'variant').all(),
        'saved_items': saved_items,
        'coupon': coupon,
        'coupon_discount': coupon_discount,
        'final_total': cart.total - coupon_discount
    }

    return render(request, 'cart/cart_detail.html', context)


@require_POST
def add_to_cart(request, product_id):
    """
    View for adding a product to the cart with proper variant handling.
    """
    product = get_object_or_404(Product, id=product_id)
    print(request.POST)

    # Check if product is active
    if product.status != 'active':
        messages.error(request, 'This product is not available')
        return redirect('products:product_detail', product_slug=product.slug)

    # Check if product is in stock
    if not product.is_in_stock:
        messages.error(request, 'This product is out of stock')
        return redirect('products:product_detail', product_slug=product.slug)

    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))

    # Get variant if specified
    variant_id = request.POST.get('variant_id')
    variant = None

    if variant_id:
        try:
            variant = ProductVariant.objects.get(id=variant_id, product=product)
            # Check if variant is in stock
            if not variant.is_in_stock:
                messages.error(request, 'This variant is out of stock')
                return redirect('products:product_detail', product_slug=product.slug)
        except ProductVariant.DoesNotExist:
            messages.error(request, 'Selected variant not found')
            return redirect('products:product_detail', product_slug=product.slug)
    elif product.variants.exists():
        # If product has variants but none selected, show error message
        messages.error(request, 'Please select all product options')
        return redirect('products:product_detail', product_slug=product.slug)

    # Check if item already exists in cart
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product, variant=variant)
        # Check available quantity
        available_qty = variant.quantity if variant else product.quantity
        if cart_item.quantity + quantity > available_qty:
            cart_item.quantity = available_qty
            messages.warning(request, f'Only {available_qty} items available. Cart updated to maximum quantity.')
        else:
            cart_item.quantity += quantity
            messages.success(request, 'Cart updated successfully')
        cart_item.save()
    except CartItem.DoesNotExist:
        # Create new cart item
        CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant,
            quantity=min(quantity, variant.quantity if variant else product.quantity)
        )
        messages.success(request, 'Product added to cart')

    return redirect('cart:cart_detail')


@require_POST
def remove_from_cart(request, item_id):
    """
    View for removing an item from the cart.
    """
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        messages.success(request, 'Item removed from cart')
    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found in cart')

    return redirect('cart:cart_detail')


@require_POST
def update_cart(request, item_id):
    """
    View for updating the quantity of an item in the cart.
    """
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0:
            cart_item.delete()
            messages.success(request, 'Item removed from cart')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully')
    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found in cart')
    except ValueError:
        messages.error(request, 'Invalid quantity')

    return redirect('cart:cart_detail')


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
    View for moving an item from the cart to the saved items list.
    """
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)

        # Check if the item already exists in saved items
        saved_item, created = SavedForLater.objects.get_or_create(
            user=request.user,
            product=cart_item.product,
            variant=cart_item.variant
        )

        # Remove from cart
        cart_item.delete()

        messages.success(request, 'Item saved for later')
    except CartItem.DoesNotExist:
        messages.error(request, 'Item not found in cart')

    return redirect('cart:cart_detail')


@login_required
@require_POST
def move_to_cart(request, item_id):
    """
    View for moving an item from the saved items list to the cart.
    """
    try:
        saved_item = SavedForLater.objects.get(id=item_id, user=request.user)
        cart = get_or_create_cart(request)

        # Check if the item already exists in the cart
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product=saved_item.product,
                variant=saved_item.variant
            )
            cart_item.quantity += 1
            cart_item.save()
        except CartItem.DoesNotExist:
            # Create new cart item
            CartItem.objects.create(
                cart=cart,
                product=saved_item.product,
                variant=saved_item.variant,
                quantity=1
            )

        # Remove from saved items
        saved_item.delete()

        messages.success(request, 'Item moved to cart')
    except SavedForLater.DoesNotExist:
        messages.error(request, 'Saved item not found')

    return redirect('cart:cart_detail')


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
