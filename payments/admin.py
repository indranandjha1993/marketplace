from django.contrib import admin
from .models import PaymentMethod, Transaction, VendorPayout


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_type', 'provider', 'is_default', 'created_at')
    list_filter = ('payment_type', 'provider', 'is_default')
    search_fields = ('user__email',)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'user', 'amount', 'status', 'transaction_type', 'created_at')
    list_filter = ('status', 'transaction_type', 'provider', 'created_at')
    search_fields = ('transaction_id', 'order__order_number', 'user__email', 'provider_transaction_id')


class VendorPayoutAdmin(admin.ModelAdmin):
    list_display = ('vendor_order', 'amount', 'status', 'payout_date', 'created_at')
    list_filter = ('status', 'payout_date', 'created_at')
    search_fields = ('vendor_order__vendor__business_name', 'vendor_order__order__order_number')


admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(VendorPayout, VendorPayoutAdmin)
