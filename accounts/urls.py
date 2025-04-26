from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.user_profile, name='user_profile'),
    path('addresses/', views.user_addresses, name='user_addresses'),
    path('addresses/add/', views.add_address, name='add_address'),
    path('addresses/edit/<int:address_id>/', views.edit_address, name='edit_address'),
    path('addresses/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('addresses/set-default/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('orders/', views.order_list, name='order_list'),
    path('order-detail/<str:order_number>/', views.order_detail, name='order_detail'),
    path('methods/', views.payment_methods, name='payment_methods'),
    path('methods/add/', views.add_payment_method, name='add_payment_method'),
    path('methods/remove/<int:method_id>/', views.remove_payment_method, name='remove_payment_method'),
    path('methods/set-default/<int:method_id>/', views.set_default_payment_method, name='set_default_payment_method'),
]
