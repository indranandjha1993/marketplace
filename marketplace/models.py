from django.db import models
from django.core.cache import cache


class CurrencySettings(models.Model):
    """
    Global currency settings for the marketplace.
    Only one instance of this model should exist.
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('INR', 'Indian Rupee (₹)'),
        ('JPY', 'Japanese Yen (¥)'),
        ('CNY', 'Chinese Yuan (¥)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('SGD', 'Singapore Dollar (S$)'),
        ('AED', 'UAE Dirham (د.إ)'),
    ]
    
    SYMBOL_POSITION_CHOICES = [
        ('before', 'Before amount (e.g., $100)'),
        ('after', 'After amount (e.g., 100$)'),
    ]
    
    currency_code = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='INR',
        help_text='Select the currency to use throughout the marketplace'
    )
    
    symbol_position = models.CharField(
        max_length=6,
        choices=SYMBOL_POSITION_CHOICES,
        default='before',
        help_text='Position of the currency symbol relative to the amount'
    )
    
    decimal_separator = models.CharField(
        max_length=1,
        default='.',
        help_text='Character to use as decimal separator'
    )
    
    thousand_separator = models.CharField(
        max_length=1,
        default=',',
        help_text='Character to use as thousand separator'
    )
    
    decimal_places = models.PositiveSmallIntegerField(
        default=2,
        help_text='Number of decimal places to display'
    )
    
    class Meta:
        verbose_name = 'Currency Settings'
        verbose_name_plural = 'Currency Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and CurrencySettings.objects.exists():
            # Update existing instance instead of creating a new one
            existing = CurrencySettings.objects.first()
            self.pk = existing.pk
        
        # Clear cache when settings are updated
        cache.delete('currency_settings')
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_currency_settings(cls):
        """
        Get the currency settings from cache or database.
        Creates default settings if none exist.
        """
        settings = cache.get('currency_settings')
        if settings is None:
            settings, created = cls.objects.get_or_create(
                pk=1,
                defaults={
                    'currency_code': 'INR',
                    'symbol_position': 'before',
                    'decimal_separator': '.',
                    'thousand_separator': ',',
                    'decimal_places': 2,
                }
            )
            cache.set('currency_settings', settings)
        return settings
    
    @property
    def currency_symbol(self):
        """Return the currency symbol based on the currency code."""
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'INR': '₹',
            'JPY': '¥',
            'CNY': '¥',
            'AUD': 'A$',
            'CAD': 'C$',
            'SGD': 'S$',
            'AED': 'د.إ',
        }
        return symbols.get(self.currency_code, self.currency_code)