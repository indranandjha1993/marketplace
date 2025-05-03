from django.contrib import admin
from .models import Order, VendorOrder, OrderItem, Payment, Refund, OrderTracking, Coupon, ShippingMethod


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'quantity', 'price', 'tax_rate', 'tax_amount', 'discount_amount', 'total')


class VendorOrderInline(admin.TabularInline):
    model = VendorOrder
    extra = 0
    readonly_fields = ('vendor', 'subtotal', 'shipping_cost', 'tax_amount', 'commission_amount', 'total_vendor_amount')


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0


class RefundInline(admin.TabularInline):
    model = Refund
    extra = 0


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'created_at')
    search_fields = ('order_number', 'user__email', 'transaction_id')
    readonly_fields = ('order_number', 'user', 'shipping_address', 'billing_address',
                       'subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total')
    inlines = [OrderItemInline, VendorOrderInline, PaymentInline, RefundInline]
    list_per_page = 20


class OrderTrackingInline(admin.TabularInline):
    model = OrderTracking
    extra = 0


class VendorOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'vendor', 'status', 'total_vendor_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'vendor__business_name')
    inlines = [OrderTrackingInline]


class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 'is_active')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_to')
    search_fields = ('code', 'description')


class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'free_shipping_threshold', 'estimated_days_min', 'estimated_days_max', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('price', 'free_shipping_threshold', 'is_active', 'display_order')


admin.site.register(Order, OrderAdmin)
admin.site.register(VendorOrder, VendorOrderAdmin)
admin.site.register(Coupon, CouponAdmin)
admin.site.register(ShippingMethod, ShippingMethodAdmin)
