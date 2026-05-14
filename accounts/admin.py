"""
MediChain Accounts Admin
Django admin configuration for custom User model and related models
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import LoginAttempt, LoginAudit, TwoFactorAuth, User, UserProfile, VerificationToken


class UserProfileInline(admin.StackedInline):
    """Inline profile editing in User admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ('bio', 'department', 'license_number', 'specialization', 'years_experience', 'avatar')
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin with role-based display"""

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'role_badge',
        'organization', 'is_verified', 'is_active', 'date_joined'
    )
    list_filter = (
        'role', 'is_verified', 'is_active', 'is_staff', 'date_joined'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'organization')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('MediChain Info', {
            'fields': ('role', 'organization', 'public_key', 'wallet_address', 'is_verified'),
            'classes': ('wide',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'role', 'organization', 'password1', 'password2'),
        }),
    )

    inlines = (UserProfileInline,)

    def role_badge(self, obj):
        """Display role as colored badge"""
        colors = {
            'ADMIN': '#f87171',
            'DOCTOR': '#38bdf8',
            'NURSE': '#7dd3fc',
            'PATIENT': '#22c55e',
            'HOSPITAL_ADMIN': '#facc15',
            'LAB_TECH': '#a78bfa',
            'INSURANCE': '#fb923c',
            'RESEARCHER': '#c084fc',
        }
        color = colors.get(obj.role, '#94a3b8')
        return format_html(
            '<span style="background:{}; color:#000; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:600;">{}</span>',
            color, obj.get_role_display()
        )
    role_badge.short_description = 'Role'


@admin.register(LoginAudit)
class LoginAuditAdmin(admin.ModelAdmin):
    """Admin for login audit logs"""

    list_display = ('audit_id', 'user_link', 'action_badge', 'ip_address', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('audit_id', 'user__username', 'ip_address')
    readonly_fields = ('audit_id', 'user', 'action', 'ip_address', 'user_agent', 'timestamp', 'details')
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/accounts/user/{}/change/">{}</a>', obj.user.id, obj.user.username)
        return 'Anonymous'
    user_link.short_description = 'User'

    def action_badge(self, obj):
        colors = {
            'LOGIN': '#22c55e',
            'LOGOUT': '#94a3b8',
            'LOGIN_FAILED': '#f87171',
            'PASSWORD_CHANGE': '#facc15',
            'TOKEN_REFRESH': '#38bdf8',
        }
        color = colors.get(obj.action, '#94a3b8')
        return format_html(
            '<span style="background:{}; color:#000; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:600;">{}</span>',
            color, obj.get_action_display()
        )
    action_badge.short_description = 'Action'


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    """Admin for two-factor authentication"""
    list_display = ('user', 'is_enabled', 'last_verified', 'created_at')
    list_filter = ('is_enabled',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('user', 'is_enabled', 'secret_key', 'last_verified', 'created_at', 'updated_at')
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or (obj and request.user == obj.user)


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """Admin for login attempts"""
    list_display = ('ip_address', 'username', 'timestamp', 'successful')
    list_filter = ('successful', 'timestamp')
    search_fields = ('ip_address', 'username')
    readonly_fields = ('ip_address', 'username', 'timestamp', 'successful')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
