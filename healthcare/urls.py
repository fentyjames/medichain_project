"""Healthcare URL configuration"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet, basename='patient')
router.register(r'hospitals', views.HospitalViewSet, basename='hospital')
router.register(r'records', views.MedicalRecordViewSet, basename='record')
router.register(r'audit', views.AuditLogViewSet, basename='audit')

urlpatterns = [
    path('api/', include(router.urls)),
]
