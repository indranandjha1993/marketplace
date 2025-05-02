from .models import CurrencySettings


def currency_settings(request):
    """
    Add currency settings to the context of all templates.
    """
    settings = CurrencySettings.get_currency_settings()
    return {
        'currency_settings': settings,
        'currency_symbol': settings.currency_symbol,
    }