"""
MediChain Accounts Forms
Custom forms for user registration, profile updates, and authentication
"""

import re
import secrets

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.validators import MinLengthValidator, RegexValidator
from django.utils.translation import gettext_lazy as _

from .models import User, UserProfile


# Custom password validators
def validate_password_strength(value):
    """Validate password strength requirements"""
    if len(value) < 12:
        raise forms.ValidationError(
            _("Password must be at least 12 characters long."),
            code='password_too_short'
        )

    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', value):
        raise forms.ValidationError(
            _("Password must contain at least one uppercase letter."),
            code='password_no_uppercase'
        )

    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', value):
        raise forms.ValidationError(
            _("Password must contain at least one lowercase letter."),
            code='password_no_lowercase'
        )

    # Check for at least one digit
    if not re.search(r'\d', value):
        raise forms.ValidationError(
            _("Password must contain at least one digit."),
            code='password_no_digit'
        )

    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise forms.ValidationError(
            _("Password must contain at least one special character."),
            code='password_no_special'
        )

    # Common-password check is handled by CommonPasswordValidator in AUTH_PASSWORD_VALIDATORS.
    return value

class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with role and organization fields"""

    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        initial='PATIENT',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    organization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Organization / Hospital',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control password-input',
            'placeholder': 'Password',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;',
            'data-strength': '0'
        }),
        help_text="Password must be at least 12 characters with uppercase, lowercase, numbers, and special characters."
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control password-input',
            'placeholder': 'Confirm Password',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role', 'organization', 'password1', 'password2')

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            validate_password_strength(password1)
        return password1

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

class UserUpdateForm(forms.ModelForm):
    """Form for updating user account information"""

    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    organization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'organization', 'phone_number')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email address is already in use by another account.")
        return email


class UserProfileForm(forms.ModelForm):
    """Form for updating extended profile information"""

    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Department',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    license_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Medical License Number',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    specialization = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Specialization',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    years_experience = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )

    class Meta:
        model = UserProfile
        fields = ('bio', 'department', 'license_number', 'specialization', 'years_experience', 'avatar')


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset via email"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("No account found with this email address.")
        return email


class TwoFactorForm(forms.Form):
    """Form for 2FA verification and setup"""
    code = forms.CharField(
        label="Verification Code",
        max_length=6,
        min_length=6,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '000000',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    backup_code = forms.CharField(
        label="Backup Code",
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter backup code',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;'
        })
    )
    enable_2fa = forms.BooleanField(
        label="Enable Two-Factor Authentication",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class AdminRegistrationForm(CustomUserCreationForm):
    """Registration form for system administrators — requires a secret access code."""

    admin_code = forms.CharField(
        label="Admin Access Code",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter admin access code',
            'style': 'background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; border-radius: 10px;',
            'autocomplete': 'off',
        })
    )

    class Meta(CustomUserCreationForm.Meta):
        fields = ('username', 'first_name', 'last_name', 'email', 'organization', 'password1', 'password2')

    def clean_admin_code(self):
        submitted = self.cleaned_data.get('admin_code', '')
        expected = getattr(settings, 'ADMIN_REGISTRATION_CODE', '')
        # Timing-safe comparison prevents brute-force timing attacks
        if not secrets.compare_digest(submitted.encode(), expected.encode()):
            raise forms.ValidationError("Invalid admin access code.")
        return submitted
