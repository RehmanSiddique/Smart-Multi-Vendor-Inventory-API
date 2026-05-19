"""
API Views for Account models.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

# Import models - these are safe
from .models import Vendor, User, OTP

# Import serializers
from .serializers import (
    UserSerializer, UserCreateSerializer, VendorSerializer, 
    UserRegistrationSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)

# Import middleware - safe
from apps.accounts.middleware import get_current_vendor

# DO NOT import from urls.py here!

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    Provides CRUD operations for users.
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """Filter users based on vendor context."""
        vendor = get_current_vendor()
        if vendor:
            return User.objects.filter(vendor=vendor)
        return User.objects.none()
    
    def get_serializer_class(self):
        """Use different serializer for create operation."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        """Get or update current user profile."""
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
            
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Vendor model.
    Only accessible by platform admins.
    """
    
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get vendor statistics."""
        vendor = self.get_object()
        data = {
            'users': vendor.users.count(),
            'products': vendor.products.count(),
            'categories': vendor.categories.count(),
            'suppliers': vendor.suppliers.count(),
            'sales': vendor.sales.count(),
            'purchase_orders': vendor.purchase_orders.count(),
        }
        return Response(data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """
    Public endpoint for user registration.
    Auto-creates vendor for new users.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    """
    Request a password reset code.
    If the email exists, an OTP code will be generated.
    """
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()
        if user:
            # Create OTP
            otp = OTP.objects.create(email=email, purpose='password_reset')
            
            # Send the OTP via email
            try:
                send_mail(
                    subject='Password Reset Code - IMS Pro',
                    message=f'Hello,\n\nYour password reset code is: {otp.code}\n\nPlease enter this code to reset your password. If you did not request this, please safely ignore this email.',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")

            # For development/testing, we still print it
            print(f"--- PASSWORD RESET CODE FOR {email}: {otp.code} ---")
            
            return Response({
                'message': 'If an account exists with this email, a reset code has been sent.'
            }, status=status.HTTP_200_OK)
            
        return Response({
            'message': 'If an account exists with this email, a reset code has been sent.'
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    """
    Reset the user's password using the OTP code.
    """
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']
        
        # Verify OTP
        otp = OTP.objects.filter(
            email=email, 
            code=code, 
            purpose='password_reset', 
            is_used=False
        ).first()
        
        if otp and otp.is_valid():
            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(new_password)
                user.save()
                
                # Mark OTP as used
                otp.is_used = True
                otp.save()
                
                return Response({
                    'message': 'Password has been reset successfully.'
                }, status=status.HTTP_200_OK)
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({
            'error': 'Invalid or expired reset code.'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)