from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/category/<slug:category_slug>/', views.product_list_by_category, name='product_list_by_category'),
    path('products/brand/<slug:brand_slug>/', views.product_list_by_brand, name='product_list_by_brand'),
    path('products/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search_products, name='search_products'),
    path('products/add-review/<slug:product_slug>/', views.add_review, name='add_review'),
    path('products/ask-question/<slug:product_slug>/', views.ask_question, name='ask_question'),
    path('products/answer-question/<int:question_id>/', views.answer_question, name='answer_question'),
]