from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('process/<str:order_number>/', views.process_payment, name='process_payment'),
    path('verify/<str:order_number>/', views.verify_payment, name='verify_payment'),
    path('success/<str:order_number>/', views.payment_success, name='payment_success'),
    path('failed/<str:order_number>/', views.payment_failed, name='payment_failed'),
    path('methods/', views.payment_methods, name='payment_methods'),
    path('methods/add/', views.add_payment_method, name='add_payment_method'),
    path('methods/remove/<int:method_id>/', views.remove_payment_method, name='remove_payment_method'),
    path('methods/set-default/<int:method_id>/', views.set_default_payment_method, name='set_default_payment_method'),
]
