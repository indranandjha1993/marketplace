from django.contrib import admin
from .models import Vendor, VendorDocument, VendorBankAccount, VendorReview


class VendorDocumentInline(admin.TabularInline):
    model = VendorDocument
    extra = 0


class VendorBankAccountInline(admin.StackedInline):
    model = VendorBankAccount
    can_delete = False


class VendorAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'verification_status', 'is_active', 'joined_date')
    list_filter = ('verification_status', 'is_active', 'city', 'state', 'country')
    search_fields = ('business_name', 'user__email', 'phone_number', 'email')
    inlines = [VendorDocumentInline, VendorBankAccountInline]


class VendorReviewAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('vendor__business_name', 'user__email', 'comment')


admin.site.register(Vendor, VendorAdmin)
admin.site.register(VendorReview, VendorReviewAdmin)
