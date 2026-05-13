"""Cross-Chain URL configuration"""
from django.urls import path
from . import views

urlpatterns = [
    path('relay/', views.RelayMessageView.as_view(), name='relay-message'),
    path('verify/', views.VerifyMessageView.as_view(), name='verify-message'),
    path('status/<str:message_id>/', views.RelayStatusView.as_view(), name='relay-status'),
    path('stats/', views.BridgeStatsView.as_view(), name='bridge-stats'),
]
