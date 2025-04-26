from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from orders.models import Order
from .serializers import (
    UserProfileDetailSerializer, UserProfileUpdateSerializer,
    UserAddressSerializer, OrderStatsSerializer
)
from ..models import UserProfile, UserAddress


class UserProfileViewSet(viewsets.GenericViewSet):
    """ViewSet for user profile operations."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return the queryset for the current user's profile."""
        return UserProfile.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return the appropriate serializer class based on the action."""
        if self.action == 'update_profile':
            return UserProfileUpdateSerializer
        return UserProfileDetailSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get the current user's profile."""
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)

        serializer = UserProfileDetailSerializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def order_stats(self, request):
        """Get order statistics for the current user."""
        stats = {
            'total': Order.objects.filter(user=request.user).count(),
            'completed': Order.objects.filter(user=request.user, status='delivered').count(),
            'processing': Order.objects.filter(
                user=request.user,
                status__in=['pending', 'processing', 'shipped']
            ).count(),
            'cancelled': Order.objects.filter(user=request.user, status='cancelled').count(),
            'total_spent': Order.objects.filter(
                user=request.user, status='delivered'
            ).aggregate(Sum('total'))['total__sum'] or 0,
        }

        serializer = OrderStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update the user profile."""
        serializer = self.get_serializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            data = serializer.validated_data
            user = request.user

            # Update user fields
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'phone_number' in data:
                user.phone_number = data['phone_number']

            # Handle password change
            new_password = data.get('new_password')
            if new_password:
                user.set_password(new_password)
                # Keep the user logged in
                update_session_auth_hash(request, user)

            user.save()

            # Update profile fields
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)

            profile_fields = [
                'address_line1', 'address_line2', 'city',
                'state', 'country', 'postal_code'
            ]

            for field in profile_fields:
                if field in data:
                    setattr(profile, field, data[field])

            profile.save()

            # Return the updated profile
            response_serializer = UserProfileDetailSerializer(profile)
            return Response(response_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for user addresses."""
    serializer_class = UserAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return addresses for the current user."""
        return UserAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Create a new address for the current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set an address as the default for its type."""
        address = self.get_object()

        # Set all addresses of same type to non-default
        UserAddress.objects.filter(
            user=request.user,
            address_type=address.address_type
        ).update(is_default=False)

        # Set this one as default
        address.is_default = True
        address.save()

        serializer = self.get_serializer(address)
        return Response(serializer.data)
