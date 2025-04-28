from .services.factory import PaymentServiceFactory


def payment_services(request):
    """
    Add payment services to the template context.
    
    Args:
        request: The current request object
        
    Returns:
        dict: Dictionary with payment services
    """
    services = PaymentServiceFactory.get_available_services(request)
    
    # Filter to only include configured services
    configured_services = {
        method: info
        for method, info in services.items()
        if info['configured'] or method == 'cod'  # Always include COD
    }
    
    return {
        'payment_services': configured_services,
        'has_payment_gateways': any(
            info['configured'] for method, info in services.items() 
            if method != 'cod'
        )
    }