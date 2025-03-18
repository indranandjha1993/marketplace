from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.vendor_list, name='vendor_list'),
    path('become-vendor/', views.become_vendor, name='become_vendor'),
    path('dashboard/', views.vendor_dashboard, name='vendor_dashboard'),
    path('dashboard/products/', views.vendor_products, name='vendor_products'),
    path('dashboard/products/add/', views.add_product, name='add_product'),
    path('dashboard/products/edit/<slug:product_slug>/', views.edit_product, name='edit_product'),
    path('dashboard/products/<slug:slug>/delete/', views.ProductDeleteView.as_view(), name='delete_product'),
    path('dashboard/orders/', views.vendor_orders, name='vendor_orders'),
    path('dashboard/order/<str:order_number>/', views.vendor_order_detail, name='vendor_order_detail'),
    path('dashboard/profile/', views.vendor_profile, name='vendor_profile'),
    path('dashboard/settings/', views.vendor_settings, name='vendor_settings'),
    path('delete-document/<int:document_id>/', views.delete_vendor_document, name='delete_document'),
    path('dashboard/analytics/', views.vendor_analytics, name='vendor_analytics'),
    path('api/attributes/<int:attribute_id>/values/', views.get_attribute_values, name='get_attribute_values'),
    path('<slug:vendor_slug>/', views.vendor_detail, name='vendor_detail'),
]
