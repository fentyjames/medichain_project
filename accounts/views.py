"""
MediChain Accounts Views
Authentication, registration, profile management, and session handling
"""

import secrets
import hashlib
import pyotp
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token

from .models import User, UserProfile, LoginAudit, VerificationToken, TwoFactorAuth, LoginAttempt
from .forms import (
    CustomUserCreationForm,
    UserProfileForm,
    UserUpdateForm,
    PasswordResetRequestForm,
    TwoFactorForm
)


# ==================== RATE LIMITING ====================
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes in seconds



def landing(request):
    """Public landing page for unauthenticated visitors"""
    # If user is authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('index')

    return render(request, 'base/landing.html')


def about(request):
    """About page with research foundation details"""

    # Threat vectors that MediChain mitigates
    threats = [
        'Man-in-the-Middle Attacks',
        'Replay Attacks',
        'Data Tampering',
        'Unauthorized Access',
        'Identity Forgery',
        'Double Spending',
        'Sybil Attacks',
        'Eavesdropping',
    ]

    context = {
        'threats': threats,
    }

    return render(request, 'base/about.html', context)


def check_rate_limit(ip_address, username=None):
    """Check if IP or username is rate limited"""
    from django.utils import timezone
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(seconds=LOCKOUT_DURATION)

    # Check IP-based rate limiting
    recent_attempts = LoginAttempt.objects.filter(
        ip_address=ip_address,
        timestamp__gte=cutoff
    )

    if username:
        recent_attempts = recent_attempts.filter(username=username)

    failed_attempts = recent_attempts.filter(successful=False).count()

    return failed_attempts >= MAX_LOGIN_ATTEMPTS

def record_login_attempt(ip_address, username, successful):
    """Record a login attempt for rate limiting"""
    LoginAttempt.objects.create(
        ip_address=ip_address,
        username=username,
        successful=successful
    )


# ==================== TEMPLATE VIEWS ====================
@login_required
def index(request):
    """Main dashboard view - renders index.html with system stats"""
    from healthcare.models import Patient, Hospital, MedicalRecord, AuditLog
    from blockchain.models import Block, Transaction, BlockchainNetwork

    stats = {
        'networks': BlockchainNetwork.objects.filter(is_active=True).count(),
        'total_blocks': Block.objects.count(),
        'total_transactions': Transaction.objects.count(),
        'patients': Patient.objects.filter(is_active=True).count(),
        'hospitals': Hospital.objects.count(),
        'medical_records': MedicalRecord.objects.filter(is_active=True).count(),
    }

    recent_logs = AuditLog.objects.select_related('record').order_by('-timestamp')[:10]

    return render(request, 'index.html', {
        'stats': stats,
        'recent_logs': recent_logs,
    })


def login_view(request):
    """Custom login view with audit logging and rate limiting"""
    if request.user.is_authenticated:
        return redirect('index')

    ip_address = get_client_ip(request)
    rate_limited = check_rate_limit(ip_address)

    if request.method == 'POST':
        if rate_limited:
            messages.error(request, 'Too many failed login attempts. Please try again later.')
            return render(request, 'accounts/login.html', {'form': AuthenticationForm(request), 'rate_limited': True})

        form = AuthenticationForm(request, data=request.POST)
        username = request.POST.get('username', '')

        if form.is_valid():
            user = form.get_user()

            # Check if 2FA is enabled
            try:
                two_factor = user.two_factor_auth
                if two_factor.is_enabled:
                    # Store user in session for 2FA verification
                    request.session['2fa_user_id'] = user.id
                    request.session['2fa_next_url'] = request.GET.get('next', 'index')

                    # Log successful login (pending 2FA)
                    LoginAudit.objects.create(
                        user=user,
                        action='LOGIN_2FA_PENDING',
                        ip_address=ip_address,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        details={'method': 'web_form', 'username': username}
                    )

                    return redirect('accounts:two_factor_verify')
            except TwoFactorAuth.DoesNotExist:
                pass

            login(request, user)

            # Log successful login
            LoginAudit.objects.create(
                user=user,
                action='LOGIN',
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'method': 'web_form'}
            )

            messages.success(request, f'Welcome back, {user.username}!')
            record_login_attempt(ip_address, username, True)

            # Redirect to next URL or index
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
        else:
            # Log failed login
            LoginAudit.objects.create(
                action='LOGIN_FAILED',
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'username_attempted': username, 'reason': 'invalid_credentials'}
            )
            record_login_attempt(ip_address, username, False)
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm(request)

    return render(request, 'accounts/login.html', {
        'form': form,
        'rate_limited': rate_limited
    })


def register_view(request):
    """User registration with role selection and email verification"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create user profile
            UserProfile.objects.create(user=user)

            # Create 2FA config (disabled by default)
            TwoFactorAuth.objects.create(user=user)

            # Generate email verification token
            token = generate_verification_token(user, 'EMAIL')

            # Send verification email (in production, use Celery for async)
            send_verification_email(request, user, token)

            # Log registration
            LoginAudit.objects.create(
                user=user,
                action='LOGIN',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                details={'method': 'registration', 'role': user.role}
            )

            messages.success(
                request,
                f'Account created successfully! Please check your email to verify your account. Welcome to MediChain, {user.username}.'
            )

            return redirect('accounts:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


def email_verification(request, token):
    """Verify user email address"""
    try:
        verification_token = VerificationToken.objects.get(
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            token_type='EMAIL',
            is_used=False
        )

        if verification_token.is_expired:
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('accounts:login')

        user = verification_token.user
        user.is_verified = True
        user.save()

        verification_token.is_used = True
        verification_token.save()

        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('accounts:login')

    except VerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('accounts:register')


def resend_verification(request):
    """Resend email verification link"""
    if request.method == 'POST':
        email = request.POST.get('email', '')
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                messages.info(request, 'This email is already verified.')
                return redirect('accounts:login')

            token = generate_verification_token(user, 'EMAIL')
            send_verification_email(request, user, token)
            messages.success(request, 'Verification email sent! Please check your inbox.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')

    return render(request, 'accounts/resend_verification.html')


@login_required
def profile_view(request):
    """User profile settings and update"""
    user = request.user

    # Ensure profile exists
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user': user,
        'form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def logout_view(request):
    """Secure logout with audit logging"""
    user = request.user

    # Log logout
    LoginAudit.objects.create(
        user=user,
        action='LOGOUT',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        details={'method': 'web'}
    )

    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('index')


@login_required
def password_change_view(request):
    """Password change with session update"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)

            LoginAudit.objects.create(
                user=user,
                action='PASSWORD_CHANGE',
                ip_address=get_client_ip(request),
                details={'method': 'web_form'}
            )

            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})


# ==================== TWO-FACTOR AUTHENTICATION ====================
@login_required
def two_factor_setup(request):
    """Setup or modify 2FA configuration"""
    user = request.user
    two_factor, created = TwoFactorAuth.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = TwoFactorForm(request.POST)
        if form.is_valid():
            if form.cleaned_data.get('enable_2fa'):
                # Generate TOTP secret and backup codes
                secret = pyotp.random_base32()
                backup_codes = [secrets.token_hex(4) for _ in range(6)]

                two_factor.is_enabled = True
                two_factor.secret_key = secret
                two_factor.backup_codes = [hashlib.sha256(code.encode()).hexdigest() for code in backup_codes]
                two_factor.save()

                messages.success(request, 'Two-factor authentication enabled!')
                return redirect('accounts:two_factor_qr')
            else:
                two_factor.is_enabled = False
                two_factor.secret_key = ''
                two_factor.backup_codes = []
                two_factor.save()
                messages.success(request, 'Two-factor authentication disabled.')
    else:
        form = TwoFactorForm()

    return render(request, 'accounts/two_factor_setup.html', {
        'form': form,
        'two_factor': two_factor
    })


def two_factor_verify(request):
    """Verify 2FA code during login"""
    user_id = request.session.get('2fa_user_id')

    if not user_id:
        return redirect('accounts:login')

    if request.method == 'POST':
        form = TwoFactorForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('code', '')
            backup_code = form.cleaned_data.get('backup_code', '')

            try:
                two_factor = TwoFactorAuth.objects.get(user_id=user_id)

                # Check backup codes first
                if backup_code:
                    backup_hash = hashlib.sha256(backup_code.strip().encode()).hexdigest()
                    if backup_hash in two_factor.backup_codes:
                        # Remove used backup code
                        two_factor.backup_codes.remove(backup_hash)
                        two_factor.save()

                        user = User.objects.get(id=user_id)
                        login(request, user)

                        LoginAudit.objects.create(
                            user=user,
                            action='LOGIN_2FA',
                            ip_address=get_client_ip(request),
                            details={'method': 'backup_code'}
                        )

                        del request.session['2fa_user_id']
                        next_url = request.session.get('2fa_next_url', 'index')
                        return redirect(next_url)

                # Verify TOTP code using pyotp
                totp = pyotp.TOTP(two_factor.secret_key)
                if totp.verify(code, valid_window=1):
                    user = User.objects.get(id=user_id)
                    login(request, user)

                    two_factor.last_verified = timezone.now()
                    two_factor.save()

                    LoginAudit.objects.create(
                        user=user,
                        action='LOGIN_2FA',
                        ip_address=get_client_ip(request),
                        details={'method': 'totp'}
                    )

                    del request.session['2fa_user_id']
                    next_url = request.session.get('2fa_next_url', 'index')
                    return redirect(next_url)

            except TwoFactorAuth.DoesNotExist:
                pass

            messages.error(request, 'Invalid verification code.')
    else:
        form = TwoFactorForm()

    return render(request, 'accounts/two_factor_verify.html', {'form': form})


# ==================== UTILITY FUNCTIONS ====================

def generate_verification_token(user, token_type, expiry_hours=24):
    """Generate and store a verification token"""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    VerificationToken.objects.create(
        user=user,
        token_type=token_type,
        token_hash=token_hash,
        expires_at=timezone.now() + timedelta(hours=expiry_hours)
    )

    return token


def send_verification_email(request, user, token):
    """Send email verification link"""
    from django.core.mail import send_mail
    from django.conf import settings

    verification_url = request.build_absolute_uri(
        reverse('accounts:email_verification', args=[token])
    )

    subject = 'Verify your MediChain account'
    message = f'''Hi {user.get_full_name() or user.username},

Welcome to MediChain! Please verify your email address by clicking the link below:

{verification_url}

If you didn't sign up, please ignore this email.

---
MediChain Healthcare Blockchain Framework
'''

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ==================== API VIEWSETS ====================

class UserViewSet(viewsets.ModelViewSet):
    """API endpoints for user management"""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter users based on requester role"""
        user = self.request.user
        if user.role == 'ADMIN':
            return User.objects.all()
        elif user.is_healthcare_provider:
            return User.objects.filter(
                Q(role__in=['PATIENT', 'DOCTOR', 'NURSE', 'HOSPITAL_ADMIN', 'LAB_TECH'])
            )
        else:
            return User.objects.filter(id=user.id)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        user = request.user
        profile = getattr(user, 'profile', None)
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'role_display': user.get_role_display(),
            'organization': user.organization,
            'is_verified': user.is_verified,
            'wallet_address': user.wallet_address,
            'date_joined': user.date_joined,
            'is_healthcare_provider': user.is_healthcare_provider,
            'can_access_records': user.can_access_records,
            'two_factor_enabled': hasattr(user, 'two_factor_auth') and user.two_factor_auth.is_enabled,
            'profile': {
                'department': profile.department if profile else '',
                'specialization': profile.specialization if profile else '',
                'license_number': profile.license_number if profile else '',
                'years_experience': profile.years_experience if profile else 0,
            } if profile else None
        })

    @action(detail=False, methods=['post'])
    def update_profile(self, request):
        """Update current user profile"""
        user = request.user
        data = request.data

        # Update user fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'organization' in data:
            user.organization = data['organization']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']

        user.save()

        # Update profile fields
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if 'department' in data:
            profile.department = data['department']
        if 'specialization' in data:
            profile.specialization = data['specialization']
        if 'license_number' in data:
            profile.license_number = data['license_number']
        if 'years_experience' in data:
            profile.years_experience = data['years_experience']

        profile.save()

        return Response({
            'status': 'profile_updated',
            'user_id': user.id,
            'username': user.username
        })

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a user (admin only)"""
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Permission denied. Admin role required.'},
                status=403
            )

        user = self.get_object()
        user.is_verified = True
        user.save()

        return Response({
            'user_id': user.id,
            'username': user.username,
            'is_verified': user.is_verified,
            'verified_by': request.user.username,
            'verified_at': timezone.now()
        })


class LoginAuditViewSet(viewsets.ViewSet):
    """API for login audit logs"""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get login audit logs for current user or all (admin)"""
        if request.user.role == 'ADMIN':
            logs = LoginAudit.objects.all()
        else:
            logs = LoginAudit.objects.filter(user=request.user)

        # Filter by action type
        action_type = request.query_params.get('action')
        if action_type:
            logs = logs.filter(action=action_type)

        logs = logs[:100]
        data = [{
            'audit_id': l.audit_id,
            'username': l.user.username if l.user else 'anonymous',
            'action': l.action,
            'action_display': l.get_action_display(),
            'ip_address': l.ip_address,
            'timestamp': l.timestamp,
            'details': l.details,
        } for l in logs]
        return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """API logout endpoint"""
    user = request.user

    # Delete auth token if exists
    Token.objects.filter(user=user).delete()

    LoginAudit.objects.create(
        user=user,
        action='LOGOUT',
        ip_address=get_client_ip(request),
        details={'method': 'api'}
    )

    return Response({
        'status': 'logged_out',
        'username': user.username,
        'timestamp': timezone.now()
    })