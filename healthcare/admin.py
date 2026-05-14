"""Healthcare admin configuration"""
from django.contrib import admin

from .models import AccessPermission, AuditLog, Hospital, InsuranceProvider, Laboratory, MedicalRecord, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'blood_type', 'is_active', 'created_at']
    search_fields = ['patient_id']

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ['name', 'license_number', 'is_verified']
    search_fields = ['name']

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['record_id', 'record_type', 'patient', 'hospital', 'created_at']
    list_filter = ['record_type', 'is_active']
    search_fields = ['record_id', 'title']

@admin.register(AccessPermission)
class AccessPermissionAdmin(admin.ModelAdmin):
    list_display = ['grantee', 'grantee_type', 'permission_type', 'is_active']
    list_filter = ['grantee_type', 'permission_type']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'actor', 'record', 'timestamp']
    list_filter = ['action', 'actor_type']
    ordering = ['-timestamp']
