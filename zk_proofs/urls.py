"""ZK Proofs URL configuration"""
from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.GenerateProofView.as_view(), name='generate-proof'),
    path('verify/', views.VerifyProofView.as_view(), name='verify-proof'),
    path('range-proof/', views.RangeProofView.as_view(), name='range-proof'),
]
