from .models import UserProfile

def user_profile_context(request):
    """
    Context processor to make user profile data available globally.
    """
    context = {}
    
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
        except (UserProfile.DoesNotExist, AttributeError):
            profile = UserProfile.objects.create(user=request.user)
        
        context['user_profile'] = profile
    
    return context