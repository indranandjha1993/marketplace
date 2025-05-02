def cart_items_count(request):
    """
    Enhanced context processor to get cart information for display in template.
    """
    count = 0
    subtotal = 0
    cart = None

    if request.user.is_authenticated:
        try:
            cart = request.user.cart
            count = cart.total_items
            subtotal = cart.subtotal
        except (AttributeError, Exception):
            pass
    else:
        # For anonymous users, get cart from session
        session_id = request.session.session_key
        if session_id:
            from cart.models import Cart
            try:
                cart = Cart.objects.get(session_id=session_id)
                count = cart.total_items
                subtotal = cart.subtotal
            except (Cart.DoesNotExist, Exception):
                pass

    # Check for saved items count
    saved_items_count = 0
    if request.user.is_authenticated:
        from cart.models import SavedForLater
        try:
            saved_items_count = SavedForLater.objects.filter(user=request.user).count()
        except Exception:
            pass

    return {
        'cart_items_count': count,
        'cart_subtotal': subtotal,
        'cart_instance': cart,
        'saved_items_count': saved_items_count,
    }
