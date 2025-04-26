from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import UserProfile, UserAddress

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone_number', 'date_joined', 'last_login']
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for the UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'address_line1', 'address_line2', 'city', 
            'state', 'country', 'postal_code'
        ]
        read_only_fields = ['id']


class UserAddressSerializer(serializers.ModelSerializer):
    """Serializer for the UserAddress model."""
    
    class Meta:
        model = UserAddress
        fields = [
            'id', 'address_type', 'is_default', 'full_name', 
            'phone', 'address_line1', 'address_line2', 'city', 
            'state', 'country', 'postal_code'
        ]
        read_only_fields = ['id']


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer that includes user and profile information."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'address_line1', 'address_line2', 
            'city', 'state', 'country', 'postal_code'
        ]
        read_only_fields = ['id', 'user']


class UserProfileUpdateSerializer(serializers.Serializer):
    """Serializer for updating both user and profile information."""
    
    # User fields
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True)
    
    # Profile fields
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Password fields
    current_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate the data, especially for password changes."""
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # If attempting to change password
        if new_password:
            if not current_password:
                raise serializers.ValidationError({"current_password": "Current password is required to set a new password"})
            
            if new_password != confirm_password:
                raise serializers.ValidationError({"confirm_password": "New passwords do not match"})
            
            user = self.context['request'].user
            if not user.check_password(current_password):
                raise serializers.ValidationError({"current_password": "Current password is incorrect"})
        
        return data


class OrderStatsSerializer(serializers.Serializer):
    """Serializer for order statistics."""
    
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    processing = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)