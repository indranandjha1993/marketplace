from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .view import UserProfileViewSet, UserAddressViewSet

router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'addresses', UserAddressViewSet, basename='addresses')

urlpatterns = [
    path('', include(router.urls)),
]
