"""Healthcare admin configuration"""
from django.contrib import admin
from django.utils.html import format_html

from .models import AccessPermission, AuditLog, Hospital, InsuranceProvider, Laboratory, MedicalRecord, Patient


def short(value, length=16):
    if not value:
        return '-'
    return f"{value[:length]}…" if len(value) > length else value


def _badge(label, color, text_color='#000'):
    return format_html(
        '<span style="background:{};color:{};padding:2px 10px;border-radius:6px;'
        'font-size:0.75rem;font-weight:600;">{}</span>',
        color, text_color, label,
    )


# ==================== PATIENT ====================

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['short_id', 'full_name', 'blood_type', 'date_of_birth', 'emergency_contact', 'active_badge', 'created_at']
    list_filter = ['is_active', 'blood_type']
    search_fields = ['patient_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['patient_id', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def short_id(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.patient_id))
    short_id.short_description = 'Patient ID'

    def full_name(self, obj):
        if obj.user:
            name = obj.user.get_full_name()
            return name if name.strip() else obj.user.username
        return '-'
    full_name.short_description = 'Name'

    def active_badge(self, obj):
        return _badge('Active', '#22c55e') if obj.is_active else _badge('Inactive', '#f87171', '#fff')
    active_badge.short_description = 'Status'


# ==================== HOSPITAL ====================

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_number', 'short_address', 'blockchain_network', 'verified_badge', 'created_at']
    list_filter = ['is_verified', 'blockchain_network']
    search_fields = ['name', 'license_number', 'address']
    readonly_fields = ['hospital_id', 'created_at']
    ordering = ['name']
    date_hierarchy = 'created_at'

    def short_address(self, obj):
        if not obj.address:
            return '-'
        return (obj.address[:50] + '…') if len(obj.address) > 50 else obj.address
    short_address.short_description = 'Address'

    def verified_badge(self, obj):
        return _badge('✓ Verified', '#22c55e') if obj.is_verified else _badge('Pending', '#facc15')
    verified_badge.short_description = 'Verification'


# ==================== LABORATORY ====================

@admin.register(Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'accreditation', 'hospital']
    list_filter = ['hospital']
    search_fields = ['name', 'accreditation']


# ==================== INSURANCE PROVIDER ====================

@admin.register(InsuranceProvider)
class InsuranceProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_number']
    search_fields = ['name', 'license_number']


# ==================== MEDICAL RECORD ====================

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['short_id', 'title', 'type_badge', 'patient', 'hospital', 'active_badge', 'created_at']
    list_filter = ['record_type', 'is_active', 'hospital']
    search_fields = ['record_id', 'title', 'description']
    readonly_fields = ['record_id', 'data_hash', 'metadata_hash', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def short_id(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.record_id))
    short_id.short_description = 'Record ID'

    def type_badge(self, obj):
        colors = {
            'DIAGNOSIS':   '#38bdf8',
            'LAB_RESULT':  '#a78bfa',
            'PRESCRIPTION':'#22c55e',
            'IMAGING':     '#fb923c',
            'SURGERY':     '#f87171',
            'DISCHARGE':   '#facc15',
            'INSURANCE':   '#c084fc',
        }
        return _badge(obj.get_record_type_display(), colors.get(obj.record_type, '#94a3b8'))
    type_badge.short_description = 'Type'

    def active_badge(self, obj):
        return _badge('Active', '#22c55e') if obj.is_active else _badge('Inactive', '#f87171', '#fff')
    active_badge.short_description = 'Status'


# ==================== ACCESS PERMISSION ====================

@admin.register(AccessPermission)
class AccessPermissionAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'grantee_type_badge', 'permission_badge', 'record', 'grantor', 'valid_until', 'active_badge']
    list_filter = ['grantee_type', 'permission_type', 'is_active']
    search_fields = ['grantee', 'record__record_id']
    readonly_fields = ['permission_id', 'created_at']
    date_hierarchy = 'created_at'

    def grantee_type_badge(self, obj):
        colors = {
            'HOSPITAL':  '#38bdf8',
            'LAB':       '#a78bfa',
            'INSURANCE': '#fb923c',
            'DOCTOR':    '#22c55e',
        }
        return _badge(obj.grantee_type, colors.get(obj.grantee_type, '#94a3b8'))
    grantee_type_badge.short_description = 'Grantee Type'

    def permission_badge(self, obj):
        colors = {
            'READ':  '#22c55e',
            'WRITE': '#facc15',
            'SHARE': '#f87171',
        }
        return _badge(obj.permission_type, colors.get(obj.permission_type, '#94a3b8'))
    permission_badge.short_description = 'Permission'

    def active_badge(self, obj):
        return _badge('Active', '#22c55e') if obj.is_active else _badge('Revoked', '#f87171', '#fff')
    active_badge.short_description = 'Status'


# ==================== AUDIT LOG ====================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action_badge', 'actor', 'actor_type_badge', 'record', 'ip_address', 'timestamp']
    list_filter = ['action', 'actor_type', 'timestamp']
    search_fields = ['actor', 'record__record_id', 'ip_address']
    readonly_fields = ['log_id', 'record', 'actor', 'actor_type', 'action', 'details', 'ip_address', 'timestamp']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def action_badge(self, obj):
        colors = {
            'CREATE':        '#22c55e',
            'READ':          '#38bdf8',
            'UPDATE':        '#facc15',
            'SHARE':         '#a78bfa',
            'DELETE':        '#f87171',
            'ACCESS_DENIED': '#ef4444',
        }
        return _badge(obj.get_action_display(), colors.get(obj.action, '#94a3b8'))
    action_badge.short_description = 'Action'

    def actor_type_badge(self, obj):
        colors = {
            'DOCTOR':   '#38bdf8',
            'HOSPITAL': '#22c55e',
            'LAB':      '#a78bfa',
            'PATIENT':  '#facc15',
            'ADMIN':    '#f87171',
        }
        return _badge(obj.actor_type, colors.get(obj.actor_type, '#94a3b8'))
    actor_type_badge.short_description = 'Actor Type'
