from django.contrib import admin
from .models import (
    Category, Brand, Product, ProductImage, ProductAttribute,
    ProductAttributeValue, ProductVariant, ProductReview,
    ProductQuestion, ProductAnswer
)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'vendor', 'category', 'price', 'status', 'quantity', 'is_digital', 'weight', 'requires_special_shipping', 'created_at')
    list_filter = ('status', 'is_featured', 'is_digital', 'requires_special_shipping', 'category', 'vendor')
    search_fields = ('title', 'description', 'sku', 'vendor__business_name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProductImageInline, ProductVariantInline]
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('vendor', 'category', 'brand', 'title', 'slug', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'sale_price', 'tax_rate', 'quantity', 'sku')
        }),
        ('Product Type & Shipping', {
            'fields': ('is_digital', 'weight', 'requires_special_shipping')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_featured', 'meta_keywords', 'meta_description')
        }),
    )


class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value')
    list_filter = ('attribute',)
    search_fields = ('value',)


class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    search_fields = ('product__title', 'user__email', 'title', 'comment')


class ProductAnswerInline(admin.TabularInline):
    model = ProductAnswer
    extra = 0


class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'question', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__title', 'user__email', 'question')
    inlines = [ProductAnswerInline]


admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(ProductAttributeValue, ProductAttributeValueAdmin)
admin.site.register(ProductReview, ProductReviewAdmin)
admin.site.register(ProductQuestion, ProductQuestionAdmin)
