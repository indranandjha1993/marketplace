from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    path('process/<str:order_number>/', views.process_payment, name='process_payment'),
    path('verify/<str:order_number>/', views.verify_payment, name='verify_payment'),
    path('success/<str:order_number>/', views.payment_success, name='payment_success'),
    path('failed/<str:order_number>/', views.payment_failed, name='payment_failed'),
]
