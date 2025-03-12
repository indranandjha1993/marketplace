from django.contrib import admin
from .models import Cart, CartItem, SavedForLater


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_id', 'total_items', 'updated_at')
    search_fields = ('user__email', 'session_id')
    inlines = [CartItemInline]


class SavedForLaterAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'variant', 'added_at')
    search_fields = ('user__email', 'product__title')


admin.site.register(Cart, CartAdmin)
admin.site.register(SavedForLater, SavedForLaterAdmin)
