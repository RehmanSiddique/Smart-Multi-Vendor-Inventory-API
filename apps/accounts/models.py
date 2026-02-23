"""
Account models for SMVIA.
Includes User, Vendor, Profile, Invitation, and OTP models.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone
from django.core.mail import send_mail
import random
import string

# Import managers - this MUST come before using them
from .managers import UserManager, VendorManager


class User(AbstractUser):
    """
    Custom User Model for SMVIA.
    
    We extend Django's AbstractUser to add:
    - Email as primary identifier
    - Role-based access control
    - Link to Vendor (for vendor users)
    """
    
    # Remove username field - we'll use email instead
    username = None
    
    # Use email as the unique identifier
    email = models.EmailField(unique=True)
    
    # Define user roles
    ROLE_CHOICES = (
        ('platform_admin', 'Platform Administrator'),  # Super admin
        ('vendor_admin', 'Vendor Administrator'),      # Can manage their vendor
        ('vendor_staff', 'Vendor Staff'),              # Can create/edit products
        ('vendor_viewer', 'Vendor Viewer'),            # Read-only access
        ('customer', 'Customer'),                       # End customer (future)
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    
    # User is not active until email verification
    is_active = models.BooleanField(default=False)
    
    # Track when user was verified
    email_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Optional phone number
    phone = models.CharField(max_length=20, blank=True)
    
    # Link to Vendor
    vendor = models.ForeignKey(
        'Vendor', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='users'
    )
    
    # Use our custom manager - UserManager is now defined above
    objects = UserManager()
    all_objects = models.Manager()  # Unfiltered (admin only)
    
    # Specify that email is the USERNAME_FIELD
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required by USERNAME_FIELD
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.role})"
    
    def get_full_name(self):
        """Return the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_short_name(self):
        """Return the short name of the user."""
        return self.first_name or self.email.split('@')[0]


class Vendor(models.Model):
    """
    Vendor/Tenant Model.
    
    Each Vendor is a separate tenant in our multi-tenant system.
    All data belongs to a vendor and is isolated.
    """
    
    # Each vendor is managed by one user (the vendor_admin)
    # This creates a one-to-one relationship with User
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='vendor_profile',
        null=True,  # Allow null temporarily
        blank=True
    )
    
    # Business information
    business_name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50, blank=True)
    
    # Tenant identifier - used in URL subdomain
    # e.g., acme.smvia.com
    subdomain = models.CharField(max_length=50, unique=True)
    
    # Contact information
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Subscription tier
    TIER_CHOICES = (
        ('basic', 'Basic - Up to 1,000 products'),
        ('professional', 'Professional - Up to 10,000 products'),
        ('enterprise', 'Enterprise - Unlimited products'),
    )
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='basic')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Add custom manager for vendor-specific queries
    objects = VendorManager()
    
    class Meta:
        db_table = 'accounts_vendor'
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
        indexes = [
            models.Index(fields=['subdomain']),
            models.Index(fields=['is_active']),
            models.Index(fields=['business_name']),
        ]
    
    def __str__(self):
        return self.business_name
    
    def get_product_limit(self):
        """Return max products based on subscription tier."""
        limits = {
            'basic': 1000,
            'professional': 10000,
            'enterprise': None,  # Unlimited
        }
        return limits.get(self.tier, 1000)
    
    def save(self, *args, **kwargs):
        """Custom save logic."""
        # Auto-create subdomain from business name if not provided
        if not self.subdomain and self.business_name:
            # Convert "Acme Corporation" to "acme-corporation"
            self.subdomain = self.business_name.lower().replace(' ', '-')
        super().save(*args, **kwargs)


class Profile(models.Model):
    """
    Extended user profile information.
    
    This is separate from User to keep User model focused on authentication.
    """
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Profile fields
    bio = models.TextField(blank=True, max_length=500)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    low_stock_alerts = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'accounts_profile'
    
    def __str__(self):
        return f"Profile for {self.user.email}"


class Invitation(models.Model):
    """
    Model for inviting new users to a vendor.
    
    When a vendor admin invites someone, we create an invitation record
    and email them a link to sign up.
    """
    
    # Use UUID for secure invitation tokens
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Who sent the invitation
    invited_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='invitations_sent'
    )
    
    # Who is being invited
    email = models.EmailField()
    role = models.CharField(
        max_length=20, 
        choices=User.ROLE_CHOICES,
        default='vendor_staff'
    )
    
    # Which vendor they'll join
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE)
    
    # Status
    is_accepted = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'accounts_invitation'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email', 'is_accepted']),
        ]
    
    def save(self, *args, **kwargs):
        """Set expiration date if not provided."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)
    
    def send_invitation_email(self):
        """Send the invitation email."""
        invite_url = f"/accept-invite/{self.token}/"
        send_mail(
            subject=f"You've been invited to join {self.vendor.business_name}",
            message=f"""
            You've been invited to join {self.vendor.business_name} as a {self.get_role_display()}.
            
            Click here to accept: {invite_url}
            
            This invitation expires on {self.expires_at.strftime('%B %d, %Y')}.
            """,
            from_email='noreply@smvia.com',
            recipient_list=[self.email],
            fail_silently=False,
        )
    
    def accept(self, user):
        """Mark invitation as accepted."""
        self.is_accepted = True
        self.accepted_at = timezone.now()
        self.save()
        
        # Add user to vendor with specified role
        user.vendor = self.vendor
        user.role = self.role
        user.save()
    
    def __str__(self):
        return f"Invitation for {self.email} to {self.vendor.business_name}"


class OTP(models.Model):
    """
    One-Time Password for email verification.
    
    Used during signup and password reset.
    """
    
    email = models.EmailField()
    code = models.CharField(max_length=6)
    
    # Purpose of this OTP
    PURPOSE_CHOICES = (
        ('signup', 'Signup Verification'),
        ('password_reset', 'Password Reset'),
        ('email_change', 'Email Change'),
    )
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='signup')
    
    # Status
    is_used = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'accounts_otp'
        indexes = [
            models.Index(fields=['email', 'code', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        """Generate code and set expiration if not provided."""
        if not self.code:
            # Generate 6-digit code
            self.code = ''.join(random.choices(string.digits, k=6))
        
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if OTP is still valid."""
        return (not self.is_used and 
                self.expires_at > timezone.now())
    
    def verify(self, code):
        """Verify the OTP code."""
        if self.code == code and self.is_valid():
            self.is_used = True
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"OTP for {self.email}: {self.code}"