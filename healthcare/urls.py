"""Healthcare URL configuration"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet, basename='patient')
router.register(r'hospitals', views.HospitalViewSet, basename='hospital')
router.register(r'records', views.MedicalRecordViewSet, basename='record')
router.register(r'audit', views.AuditLogViewSet, basename='audit')

# API patterns — included at /api/healthcare/
urlpatterns = [
    path('api/', include(router.urls)),
]

# Template patterns — included at /healthcare/
template_urlpatterns = [
    path('', views.healthcare_dashboard, name='healthcare_dashboard'),
    # Patients
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_add, name='patient_add'),
    path('patients/export/csv/', views.export_patients_csv, name='export_patients_csv'),
    path('patients/<str:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<str:patient_id>/report/', views.patient_report, name='patient_report'),
    path('patients/<str:patient_id>/report/print/', views.patient_print_report, name='patient_print_report'),
    path('patients/<str:patient_id>/edit/', views.patient_edit, name='patient_edit'),
    path('patients/<str:patient_id>/delete/', views.patient_delete, name='patient_delete'),
    # Hospitals
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospitals/add/', views.hospital_add, name='hospital_add'),
    path('hospitals/<str:hospital_id>/', views.hospital_detail, name='hospital_detail'),
    path('hospitals/<str:hospital_id>/report/', views.hospital_report, name='hospital_report'),
    path('hospitals/<str:hospital_id>/report/print/', views.hospital_print_report, name='hospital_print_report'),
    path('hospitals/<str:hospital_id>/edit/', views.hospital_edit, name='hospital_edit'),
    path('hospitals/<str:hospital_id>/delete/', views.hospital_delete, name='hospital_delete'),
    # Records
    path('records/', views.record_list, name='record_list'),
    path('records/add/', views.record_add, name='record_add'),
    path('records/export/csv/', views.export_records_csv, name='export_records_csv'),
    path('records/<str:record_id>/', views.record_detail, name='record_detail'),
    path('records/<str:record_id>/edit/', views.record_edit, name='record_edit'),
    path('records/<str:record_id>/archive/', views.record_archive, name='record_archive'),
    path('records/<str:record_id>/report/', views.record_report, name='record_report'),
    path('records/<str:record_id>/report/print/', views.record_print_report, name='record_print_report'),
    # Laboratories
    path('labs/', views.laboratory_list, name='laboratory_list'),
    path('labs/add/', views.laboratory_add, name='laboratory_add'),
    path('labs/<str:lab_id>/', views.laboratory_detail, name='laboratory_detail'),
    path('labs/<str:lab_id>/edit/', views.laboratory_edit, name='laboratory_edit'),
    path('labs/<str:lab_id>/delete/', views.laboratory_delete, name='laboratory_delete'),
    path('labs/<str:lab_id>/report/', views.laboratory_report, name='laboratory_report'),
    path('labs/<str:lab_id>/report/print/', views.laboratory_print_report, name='laboratory_print_report'),
    # Insurance Providers
    path('insurance/', views.insurance_list, name='insurance_list'),
    path('insurance/add/', views.insurance_add, name='insurance_add'),
    path('insurance/<str:provider_id>/', views.insurance_detail, name='insurance_detail'),
    path('insurance/<str:provider_id>/edit/', views.insurance_edit, name='insurance_edit'),
    path('insurance/<str:provider_id>/delete/', views.insurance_delete, name='insurance_delete'),
    path('insurance/<str:provider_id>/report/', views.insurance_report, name='insurance_report'),
    path('insurance/<str:provider_id>/report/print/', views.insurance_print_report, name='insurance_print_report'),
    # Permissions
    path('permissions/', views.permission_list, name='permission_list'),
    path('permissions/add/', views.permission_add, name='permission_add'),
    path('permissions/<str:permission_id>/revoke/', views.permission_revoke, name='permission_revoke'),
    # Audit Log
    path('audit/', views.audit_log_list, name='audit_log_list'),
    path('audit/export/csv/', views.export_audit_csv, name='export_audit_csv'),
    # Reports hub + individual reports
    path('reports/', views.reports_hub, name='reports_hub'),
    path('reports/overview/', views.system_overview_report, name='system_overview_report'),
    path('reports/overview/print/', views.system_overview_print_report, name='system_overview_print_report'),
    path('reports/audit/', views.audit_compliance_report, name='audit_compliance_report'),
    path('reports/audit/print/', views.audit_compliance_print_report, name='audit_compliance_print_report'),
]
