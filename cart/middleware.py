from django.utils.deprecation import MiddlewareMixin


class CartMiddleware(MiddlewareMixin):
    """
    Middleware to migrate cart from session to user on login.
    """

    def process_response(self, request, response):
        """
        Process response to check for user login and migrate cart if needed.
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check if there's a session key and the user just logged in
            session_id = request.session.session_key
            just_logged_in = request.session.get('_auth_user_id') and not request.session.get('cart_migrated')

            if just_logged_in and session_id:
                # Import here to avoid circular import
                from .models import Cart

                # Migrate cart from session to user
                try:
                    Cart().migrate_from_session(request.user, session_id)
                    # Mark cart as migrated to prevent multiple migrations
                    request.session['cart_migrated'] = True
                except Exception as e:
                    # Log the error but don't break the response
                    print(f"Error migrating cart: {str(e)}")

        return response
