from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, UserAddress

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('email', 'first_name', 'last_name', 'is_vendor', 'is_staff', 'is_active')
    list_filter = ('is_vendor', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone_number')}),
        (_('Permissions'), {'fields': ('is_active', 'is_vendor', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)

class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'address_type', 'city', 'is_default')
    list_filter = ('address_type', 'is_default', 'city', 'state', 'country')
    search_fields = ('user__email', 'full_name', 'address_line1', 'city', 'postal_code')

admin.site.register(User, UserAdmin)
admin.site.register(UserAddress, UserAddressAdmin)


# vendors/admin.py



# products/admin.py



# orders/admin.py


# cart/admin.py



# payments/admin.py

