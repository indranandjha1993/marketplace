from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('save-for-later/<int:item_id>/', views.save_for_later, name='save_for_later'),
    path('move-to-cart/<int:item_id>/', views.move_to_cart, name='move_to_cart'),
    path('remove-from-saved/<int:item_id>/', views.remove_from_saved, name='remove_from_saved'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('move-all-to-cart/', views.move_all_to_cart, name='move_all_to_cart'),
    path('clear-saved-items/', views.clear_saved_items, name='clear_saved_items'),
    path('update-shipping/', views.update_shipping_method, name='update_shipping'),
]
