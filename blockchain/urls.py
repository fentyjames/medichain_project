"""Blockchain app URL configuration"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'networks', views.BlockchainNetworkViewSet, basename='network')
router.register(r'blocks', views.BlockViewSet, basename='block')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'rollup', views.RollupViewSet, basename='rollup')
router.register(r'consensus', views.ConsensusViewSet, basename='consensus')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/dashboard/', views.DashboardView.as_view(), name='api_dashboard'),
]
