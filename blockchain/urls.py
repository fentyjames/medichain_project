"""Blockchain app URL configuration"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'networks', views.BlockchainNetworkViewSet, basename='network')
router.register(r'blocks', views.BlockViewSet, basename='block')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')
router.register(r'rollup', views.RollupViewSet, basename='rollup')
router.register(r'consensus', views.ConsensusViewSet, basename='consensus')

# API patterns — included at /api/blockchain/
urlpatterns = [
    path('api/', include(router.urls)),
    path('api/dashboard/', views.DashboardView.as_view(), name='api_dashboard'),
]

# Template patterns — included at /blockchain/
template_urlpatterns = [
    path('', views.blockchain_dashboard, name='blockchain_dashboard'),
    path('blocks/', views.block_list, name='block_list'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/add/', views.transaction_add, name='transaction_add'),
    path('transactions/export/csv/', views.export_transactions_csv, name='export_transactions_csv'),
    path('rollups/', views.rollup_list, name='rollup_list'),
    path('rollups/create/', views.rollup_create, name='rollup_create'),
    path('blocks/<int:block_number>/', views.block_detail, name='block_detail'),
    path('transactions/<str:tx_hash>/', views.transaction_detail, name='transaction_detail'),
    path('rollups/<str:batch_id>/', views.rollup_detail, name='rollup_detail'),
]
