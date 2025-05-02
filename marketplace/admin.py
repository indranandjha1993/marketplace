from django.contrib import admin
from django.utils.html import format_html
from .models import CurrencySettings


@admin.register(CurrencySettings)
class CurrencySettingsAdmin(admin.ModelAdmin):
    list_display = ('get_currency_display', 'symbol_position', 'decimal_places')
    fieldsets = (
        ('Currency', {
            'fields': ('currency_code',)
        }),
        ('Format Settings', {
            'fields': ('symbol_position', 'decimal_separator', 'thousand_separator', 'decimal_places')
        }),
    )
    
    def get_currency_display(self, obj):
        """Display currency code with symbol."""
        return format_html('{} <span style="color: #666;">({} )</span>', 
                          obj.get_currency_code_display(), 
                          obj.currency_symbol)
    get_currency_display.short_description = 'Currency'
    
    def has_add_permission(self, request):
        # Only allow adding if no settings exist
        return not CurrencySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deleting the settings
        return False