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
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_add, name='patient_add'),
    path('patients/<str:patient_id>/', views.patient_detail, name='patient_detail'),
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospitals/add/', views.hospital_add, name='hospital_add'),
    path('hospitals/<str:hospital_id>/', views.hospital_detail, name='hospital_detail'),
    path('records/', views.record_list, name='record_list'),
    path('records/add/', views.record_add, name='record_add'),
    path('records/<str:record_id>/', views.record_detail, name='record_detail'),
    path('permissions/add/', views.permission_add, name='permission_add'),
]
