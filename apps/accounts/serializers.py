"""
Serializers for Account models.
Convert Django models to JSON and validate incoming data.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vendor, User

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    Handles user data including roles and vendor relationships.
    """
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active']
        read_only_fields = ['id', 'is_active']


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    Includes password handling.
    """
    
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'role', 'phone']
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class VendorSerializer(serializers.ModelSerializer):
    """
    Serializer for Vendor/Tenant model.
    """
    
    user_count = serializers.IntegerField(source='users.count', read_only=True)
    product_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'business_name', 'subdomain', 'tier',
            'is_active', 'created_at', 'user_count', 'product_count'
        ]
        read_only_fields = ['id', 'created_at']