"""Main API URL configuration"""
from django.urls import path

from . import views

urlpatterns = [
    path('auth/login/', views.AuthView.as_view(), name='api-login'),
    path('dashboard/', views.DashboardView.as_view(), name='api-dashboard'),
    path('networks/status/', views.NetworkStatusView.as_view(), name='network-status'),
    path('rollup/create/', views.CreateRollupView.as_view(), name='api-create-rollup'),
    path('rollup/submit/', views.SubmitRollupView.as_view(), name='api-submit-rollup'),
    path('cross-chain/transfer/', views.CrossChainTransferView.as_view(), name='api-cross-chain-transfer'),
    path('zk/verify/', views.VerifyZKProofView.as_view(), name='api-verify-zk'),
    path('merkle/', views.MerkleTreeView.as_view(), name='api-merkle-tree'),
    path('patients/<str:patient_id>/records/', views.PatientRecordsView.as_view(), name='api-patient-records'),
    path('records/<str:record_id>/grant-access/', views.GrantAccessView.as_view(), name='api-grant-access'),
    path('records/<str:record_id>/audit/', views.AuditTrailView.as_view(), name='api-audit-trail'),
]
