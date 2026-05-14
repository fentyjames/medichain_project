"""Cross-Chain URL configuration"""
from django.urls import path
from . import views

# API patterns — included at /api/cross-chain/
urlpatterns = [
    path('relay/', views.RelayMessageView.as_view(), name='relay-message'),
    path('verify/', views.VerifyMessageView.as_view(), name='verify-message'),
    path('status/<str:message_id>/', views.RelayStatusView.as_view(), name='relay-status'),
    path('stats/', views.BridgeStatsView.as_view(), name='bridge-stats'),
]

# Template patterns — included at /cross-chain/
template_urlpatterns = [
    path('', views.crosschain_dashboard, name='crosschain_dashboard'),
    path('transfer/', views.crosschain_transfer, name='crosschain_transfer'),
    path('<str:message_id>/', views.crosschain_detail, name='crosschain_detail'),
]
