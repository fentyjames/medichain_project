"""ZK Proofs URL configuration"""
from django.urls import path

from . import views

# API patterns — included at /api/zk-proofs/
urlpatterns = [
    path('generate/', views.GenerateProofView.as_view(), name='generate-proof'),
    path('verify/', views.VerifyProofView.as_view(), name='verify-proof'),
    path('range-proof/', views.RangeProofView.as_view(), name='range-proof'),
]

# Template patterns — included at /zk-proofs/
template_urlpatterns = [
    path('', views.zk_dashboard, name='zk_dashboard'),
    path('generate/', views.zk_generate, name='zk_generate'),
    path('verify/', views.zk_verify_page, name='zk_verify_page'),
    path('range/', views.zk_range, name='zk_range'),
]
