def cart_items_count(request):
    """
    Context processor to get cart items count for display in template.
    """
    count = 0

    if request.user.is_authenticated:
        try:
            count = request.user.cart.total_items
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
            except (Cart.DoesNotExist, Exception):
                pass

    return {'cart_items_count': count}
