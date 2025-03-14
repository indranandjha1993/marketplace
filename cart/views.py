from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.db import transaction

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

        cart, _ = Cart.objects.get_or_create(session_id=session_id, user__isnull=True)

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

    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('product', 'variant', 'product__vendor').all(),
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
    Supports both regular form submission and AJAX requests.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    try:
        with transaction.atomic():
            product = get_object_or_404(Product, id=product_id, status='active')

            # Check if product is active
            if product.status != 'active':
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': 'This product is not available',
                    }, status=400)
                messages.error(request, 'This product is not available')
                return redirect('products:product_detail', product_slug=product.slug)

            # Check if product is in stock
            if not product.is_in_stock:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': 'This product is out of stock',
                    }, status=400)
                messages.error(request, 'This product is out of stock')
                return redirect('products:product_detail', product_slug=product.slug)

            cart = get_or_create_cart(request)

            try:
                quantity = int(request.POST.get('quantity', 1))
                if quantity <= 0:
                    raise ValueError("Quantity must be greater than zero")
            except ValueError:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': 'Invalid quantity',
                    }, status=400)
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
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': 'Please select a product variant',
                            'requires_variant': True,
                        }, status=400)
                    messages.error(request, 'Please select a product variant')
                    return redirect('products:product_detail', product_slug=product.slug)

                try:
                    # Get the selected variant
                    variant = ProductVariant.objects.get(id=variant_id, product=product)

                    # Check if variant is in stock
                    if not variant.is_in_stock:
                        if is_ajax:
                            return JsonResponse({
                                'success': False,
                                'message': 'This variant is out of stock',
                            }, status=400)
                        messages.error(request, 'This variant is out of stock')
                        return redirect('products:product_detail', product_slug=product.slug)

                except ProductVariant.DoesNotExist:
                    if is_ajax:
                        return JsonResponse({
                            'success': False,
                            'message': 'Selected variant not found',
                        }, status=400)
                    messages.error(request, 'Selected variant not found')
                    return redirect('products:product_detail', product_slug=product.slug)

            # Check if item already exists in cart
            try:
                cart_item = CartItem.objects.get(cart=cart, product=product, variant=variant)
                # Check available quantity
                available_qty = variant.quantity if variant else product.quantity

                if cart_item.quantity + quantity > available_qty:
                    cart_item.quantity = available_qty
                    cart_item.save()

                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'message': f'Only {available_qty} items available. Cart updated to maximum quantity.',
                            'cart_count': cart.total_items,
                            'cart_total': float(cart.total),
                        })

                    messages.warning(request,
                                     f'Only {available_qty} items available. Cart updated to maximum quantity.')
                else:
                    cart_item.quantity += quantity
                    cart_item.save()

                    if is_ajax:
                        return JsonResponse({
                            'success': True,
                            'message': 'Cart updated successfully',
                            'cart_count': cart.total_items,
                            'cart_total': float(cart.total),
                        })

                    messages.success(request, 'Cart updated successfully')
            except CartItem.DoesNotExist:
                # Calculate max quantity based on available stock
                available_qty = variant.quantity if variant else product.quantity
                add_quantity = min(quantity, available_qty)

                # Create new cart item
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    quantity=add_quantity
                )

                if is_ajax:
                    product_name = product.title
                    if variant:
                        variant_details = ', '.join([f"{val.attribute.name}: {val.value}"
                                                     for val in variant.attribute_values.all()])
                        product_name = f"{product_name} ({variant_details})"

                    return JsonResponse({
                        'success': True,
                        'message': f'{product_name} added to cart',
                        'cart_count': cart.total_items,
                        'cart_total': float(cart.total),
                    })

                messages.success(request, 'Product added to cart')

            # If we get here without returning, we need to redirect
            return redirect('cart:cart_detail')

    except Exception as e:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': f'Error adding to cart: {str(e)}',
            }, status=500)
        messages.error(request, f'Error adding to cart: {str(e)}')
        return redirect('products:product_detail', product_slug=product.slug)


@require_POST
def remove_from_cart(request, item_id):
    """
    View for removing an item from the cart.
    Supports both regular form submission and AJAX requests.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        product_name = cart_item.product.title

        if cart_item.variant:
            variant_details = ', '.join([f"{val.attribute.name}: {val.value}"
                                         for val in cart_item.variant.attribute_values.all()])
            product_name = f"{product_name} ({variant_details})"

        cart_item.delete()

        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': f'{product_name} removed from cart',
                'cart_count': cart.total_items,
                'cart_total': float(cart.total),
                'item_id': item_id,
            })

        messages.success(request, 'Item removed from cart')
    except CartItem.DoesNotExist:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart',
            }, status=404)

        messages.error(request, 'Item not found in cart')

    return redirect('cart:cart_detail')


@require_POST
def update_cart(request, item_id):
    """
    View for updating the quantity of an item in the cart.
    Supports both regular form submission and AJAX requests.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)

        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid quantity',
                }, status=400)

            messages.error(request, 'Invalid quantity')
            return redirect('cart:cart_detail')

        if quantity <= 0:
            cart_item.delete()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Item removed from cart',
                    'cart_count': cart.total_items,
                    'cart_total': float(cart.total),
                    'item_removed': True,
                    'item_id': item_id,
                })

            messages.success(request, 'Item removed from cart')
        else:
            # Check if requested quantity is available
            available_qty = cart_item.variant.quantity if cart_item.variant else cart_item.product.quantity

            if quantity > available_qty:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': f'Only {available_qty} items available',
                        'available_quantity': available_qty,
                    }, status=400)

                messages.warning(request, f'Only {available_qty} items available')
                quantity = available_qty

            cart_item.quantity = quantity
            cart_item.save()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Cart updated successfully',
                    'cart_count': cart.total_items,
                    'cart_total': float(cart.total),
                    'item_total': float(cart_item.total),
                    'item_subtotal': float(cart_item.subtotal),
                    'item_quantity': cart_item.quantity,
                })

            messages.success(request, 'Cart updated successfully')
    except CartItem.DoesNotExist:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart',
            }, status=404)

        messages.error(request, 'Item not found in cart')

    return redirect('cart:cart_detail')


@require_POST
def clear_cart(request):
    """
    View for clearing all items from the cart.
    Supports both regular form submission and AJAX requests.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    cart = get_or_create_cart(request)
    cart.clear()

    # Remove coupon if applied
    if 'coupon_id' in request.session:
        del request.session['coupon_id']

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': 'Cart cleared successfully',
            'cart_count': 0,
            'cart_total': 0,
        })

    messages.success(request, 'Cart cleared successfully')
    return redirect('cart:cart_detail')


@login_required
@require_POST
def save_for_later(request, item_id):
    """
    View for moving an item from the cart to the saved items list.
    Supports both regular form submission and AJAX requests.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        product_name = cart_item.product.title

        # Check if the item already exists in saved items
        saved_item, created = SavedForLater.objects.get_or_create(
            user=request.user,
            product=cart_item.product,
            variant=cart_item.variant
        )

        # Remove from cart
        cart_item.delete()

        if is_ajax:
            return JsonResponse({
                'success': True,
                'message': f'{product_name} saved for later',
                'cart_count': cart.total_items,
                'cart_total': float(cart.total),
                'item_id': item_id,
            })

        messages.success(request, 'Item saved for later')
    except CartItem.DoesNotExist:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': 'Item not found in cart',
            }, status=404)

        messages.error(request, 'Item not found in cart')

    return redirect('cart:cart_detail')


@login_required
@require_POST
def move_to_cart(request, item_id):
    """
    View for moving an item from the saved items list to the cart.
    Supports both regular form submission and AJAX requests.
    """
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    try:
        saved_item = SavedForLater.objects.get(id=item_id, user=request.user)
        cart = get_or_create_cart(request)
        product_name = saved_item.product.title

        # Check if the product is still active and in stock
        product = saved_item.product
        if product.status != 'active':
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'This product is no longer available',
                }, status=400)

            messages.error(request, 'This product is no longer available')
            saved_item.delete()  # Remove unavailable product from saved items
            return redirect('cart:cart_detail')

        if not product.is_in_stock:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'This product is out of stock',
                }, status=400)

            messages.error(request, 'This product is out of stock')
            return redirect('cart:cart_detail')

        # If it's a variant, check variant status
        if saved_item.variant:
            if not saved_item.variant.is_in_stock:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': 'This product variant is out of stock',
                    }, status=400)

                messages.error(request, 'This product variant is out of stock')
                return redirect('cart:cart_detail')

        # Check if the item already exists in the cart
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product=saved_item.product,
                variant=saved_item.variant
            )

            # Check available quantity before updating
            available_qty = saved_item.variant.quantity if saved_item.variant else saved_item.product.quantity

            if cart_item.quantity + 1 > available_qty:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': f'Cannot add more of this item. Maximum quantity ({available_qty}) already in cart.',
                    }, status=400)

                messages.warning(request,
                                 f'Cannot add more of this item. Maximum quantity ({available_qty}) already in cart.')
            else:
                cart_item.quantity += 1
                cart_item.save()

                # Remove from saved items
                saved_item.delete()

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': f'{product_name} moved to cart',
                        'cart_count': cart.total_items,
                        'cart_total': float(cart.total),
                        'item_id': item_id,
                    })

                messages.success(request, 'Item moved to cart')
        except CartItem.DoesNotExist:
            # Create new cart item with quantity 1
            CartItem.objects.create(
                cart=cart,
                product=saved_item.product,
                variant=saved_item.variant,
                quantity=1
            )

            # Remove from saved items
            saved_item.delete()

            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'{product_name} moved to cart',
                    'cart_count': cart.total_items,
                    'cart_total': float(cart.total),
                    'item_id': item_id,
                })

            messages.success(request, 'Item moved to cart')
    except SavedForLater.DoesNotExist:
        if is_ajax:
            return JsonResponse({
                'success': False,
                'message': 'Saved item not found',
            }, status=404)

        messages.error(request, 'Saved item not found')

    return redirect('cart:cart_detail')


def get_cart_info(request):
    """
    AJAX endpoint to get current cart information without refreshing the page.
    """
    try:
        cart = get_or_create_cart(request)

        # Calculate coupon discount if applied
        coupon_discount = 0
        coupon_id = request.session.get('coupon_id')

        if coupon_id:
            from orders.models import Coupon
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                if coupon.is_valid:
                    coupon_discount = coupon.calculate_discount(cart.subtotal)
            except Coupon.DoesNotExist:
                pass

        cart_data = {
            'success': True,
            'cart_count': cart.total_items,
            'subtotal': float(cart.subtotal),
            'tax_amount': float(cart.tax_amount),
            'coupon_discount': float(coupon_discount),
            'total': float(cart.total - coupon_discount),
            'items': []
        }

        # Add detailed item info
        for item in cart.items.select_related('product', 'variant').all():
            product_name = item.product.title
            if item.variant:
                variant_details = ', '.join([f"{val.attribute.name}: {val.value}"
                                             for val in item.variant.attribute_values.all()])
                product_name = f"{product_name} ({variant_details})"

            cart_data['items'].append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': product_name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'subtotal': float(item.subtotal),
                'total': float(item.total),
                'image_url': item.product.primary_image.image.url if item.product.primary_image else None,
            })

        return JsonResponse(cart_data)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
        }, status=500)


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
