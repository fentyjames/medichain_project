"""
MediChain Accounts Models
Custom User authentication with role-based access control
"""

import hashlib
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinLengthValidator


class User(AbstractUser):
    """Custom User model for MediChain with role-based access"""

    ROLE_CHOICES = [
        ('ADMIN', 'System Administrator'),
        ('DOCTOR', 'Doctor'),
        ('NURSE', 'Nurse'),
        ('PATIENT', 'Patient'),
        ('HOSPITAL_ADMIN', 'Hospital Administrator'),
        ('LAB_TECH', 'Laboratory Technician'),
        ('INSURANCE', 'Insurance Agent'),
        ('RESEARCHER', 'Medical Researcher'),
    ]

    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='PATIENT',
        help_text="User role in the healthcare system"
    )
    organization = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Hospital, lab, or institution affiliation"
    )
    public_key = models.TextField(
        blank=True,
        help_text="Blockchain public key for this user"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Identity verification status"
    )
    wallet_address = models.CharField(
        max_length=64, 
        blank=True,
        help_text="Ethereum/Blockchain wallet address"
    )
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_users'
        ordering = ['-date_joined']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_healthcare_provider(self):
        """Check if user is a healthcare provider"""
        return self.role in ['DOCTOR', 'NURSE', 'HOSPITAL_ADMIN', 'LAB_TECH']

    @property
    def is_patient_user(self):
        """Check if user is a patient"""
        return self.role == 'PATIENT'

    @property
    def can_access_records(self):
        """Check if user has permission to access medical records"""
        return self.role in ['ADMIN', 'DOCTOR', 'NURSE', 'HOSPITAL_ADMIN', 'LAB_TECH']


class UserProfile(models.Model):
    """Extended profile information for MediChain users"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    bio = models.TextField(blank=True)
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True,
        null=True
    )
    department = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Medical license or professional certification number"
    )
    specialization = models.CharField(max_length=100, blank=True)
    years_experience = models.PositiveIntegerField(default=0)

    # Blockchain identity
    identity_hash = models.CharField(
        max_length=64, 
        blank=True,
        help_text="SHA-256 hash of verified identity documents"
    )

    class Meta:
        db_table = 'accounts_profiles'

    def __str__(self):
        return f"Profile-{self.user.username}"

    def generate_identity_hash(self):
        """Generate identity hash from user data"""
        identity_data = f"{self.user.username}_{self.user.email}_{self.license_number}"
        self.identity_hash = hashlib.sha256(identity_data.encode()).hexdigest()
        self.save()
        return self.identity_hash


class LoginAudit(models.Model):
    """Audit trail for user authentication events"""
    ACTION_TYPES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('LOGIN_FAILED', 'Failed Login Attempt'),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('TOKEN_REFRESH', 'Token Refreshed'),
    ]

    audit_id = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='login_audits'
    )
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'accounts_login_audits'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit-{self.action}-{self.timestamp}"

    def save(self, *args, **kwargs):
        if not self.audit_id:
            self.audit_id = hashlib.sha256(
                f"audit_{uuid.uuid4()}_{timezone.now().timestamp()}".encode()
            ).hexdigest()
        super().save(*args, **kwargs)


class VerificationToken(models.Model):
    """Email/Identity verification tokens"""
    TOKEN_TYPES = [
        ('EMAIL', 'Email Verification'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('IDENTITY', 'Identity Verification'),
    ]

    token_id = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens'
    )
    token_type = models.CharField(max_length=20, choices=TOKEN_TYPES)
    token_hash = models.CharField(max_length=64)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'accounts_verification_tokens'
        ordering = ['-created_at']

    def __str__(self):
        return f"Token-{self.token_type}-{self.user.username}"

    def save(self, *args, **kwargs):
        if not self.token_id:
            self.token_id = hashlib.sha256(
                f"token_{uuid.uuid4()}_{timezone.now().timestamp()}".encode()
            ).hexdigest()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired


class TwoFactorAuth(models.Model):
    """Two-factor authentication configuration per user"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='two_factor_auth'
    )
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=32, blank=True)
    backup_codes = models.JSONField(default=list, blank=True,
        help_text="List of one-time backup codes (hashed)")
    last_verified = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accounts_two_factor_auth'
        verbose_name = 'Two-Factor Authentication'
        verbose_name_plural = 'Two-Factor Authentications'

    def __str__(self):
        return f"2FA-{self.user.username}-{'Enabled' if self.is_enabled else 'Disabled'}"


class LoginAttempt(models.Model):
    """Rate limiting and login attempt tracking"""
    ip_address = models.GenericIPAddressField()
    username = models.CharField(max_length=150, blank=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    successful = models.BooleanField(default=False)

    class Meta:
        db_table = 'accounts_login_attempts'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['username', 'timestamp']),
        ]

    def __str__(self):
        return f"LoginAttempt-{self.ip_address}-{'Success' if self.successful else 'Failed'}"
