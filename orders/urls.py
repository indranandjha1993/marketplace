from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('checkout/', views.checkout, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-success/<str:order_number>/', views.order_success, name='order_success'),
    path('order-detail/<str:order_number>/', views.order_detail, name='order_detail'),
    path('cancel-order/<str:order_number>/', views.cancel_order, name='cancel_order'),
    path('return-order/<str:order_number>/', views.return_order, name='return_order'),
    path('track-order/<str:order_number>/', views.track_order, name='track_order'),
    path('generate-invoice/<str:order_number>/', views.generate_invoice, name='generate_invoice'),
]
