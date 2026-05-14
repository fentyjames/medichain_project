"""MediChain URL Configuration"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts import views as accounts_views  # Import for default redirect


# Import template views
from blockchain import views as blockchain_views
from healthcare import views as healthcare_views
from cross_chain import views as cross_chain_views
from zk_proofs import views as zk_views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

# ==================== PUBLIC PAGES ====================
    path('', accounts_views.landing, name='landing'),           # Public landing page
    path('dashboard/', accounts_views.index, name='index'),      # Authenticated dashboard
    path('about/', accounts_views.about, name='about'),          # About/Research page
    
    # Accounts
    path('accounts/', include('accounts.urls', namespace='accounts')),
    
    # Main Dashboard
    #path('', accounts_views.index, name='index'),
    #path('', blockchain_views.index, name='index'),

    # Blockchain Template Views
    path('blockchain/', blockchain_views.blockchain_dashboard, name='blockchain_dashboard'),
    path('blockchain/blocks/', blockchain_views.block_list, name='block_list'),
    path('blockchain/transactions/', blockchain_views.transaction_list, name='transaction_list'),
    path('blockchain/transactions/add/', blockchain_views.transaction_add, name='transaction_add'),
    path('blockchain/rollups/', blockchain_views.rollup_list, name='rollup_list'),
    path('blockchain/rollups/create/', blockchain_views.rollup_create, name='rollup_create'),

    # Healthcare Template Views
    path('healthcare/', healthcare_views.healthcare_dashboard, name='healthcare_dashboard'),
    path('healthcare/patients/', healthcare_views.patient_list, name='patient_list'),
    path('healthcare/patients/add/', healthcare_views.patient_add, name='patient_add'),
    path('healthcare/patients/<str:patient_id>/', healthcare_views.patient_detail, name='patient_detail'),
    path('healthcare/hospitals/', healthcare_views.hospital_list, name='hospital_list'),
    path('healthcare/hospitals/add/', healthcare_views.hospital_add, name='hospital_add'),
    path('healthcare/hospitals/<str:hospital_id>/', healthcare_views.hospital_detail, name='hospital_detail'),
    path('healthcare/records/', healthcare_views.record_list, name='record_list'),
    path('healthcare/records/add/', healthcare_views.record_add, name='record_add'),
    path('healthcare/records/<str:record_id>/', healthcare_views.record_detail, name='record_detail'),
    path('healthcare/permissions/add/', healthcare_views.permission_add, name='permission_add'),

    # Cross-Chain Template Views
    path('cross-chain/', cross_chain_views.crosschain_dashboard, name='crosschain_dashboard'),
    path('cross-chain/transfer/', cross_chain_views.crosschain_transfer, name='crosschain_transfer'),
    path('cross-chain/<str:message_id>/', cross_chain_views.crosschain_detail, name='crosschain_detail'),

    # ZK Proofs Template Views
    path('zk-proofs/', zk_views.zk_dashboard, name='zk_dashboard'),
    path('zk-proofs/generate/', zk_views.zk_generate, name='zk_generate'),
    path('zk-proofs/verify/', zk_views.zk_verify_page, name='zk_verify_page'),
    path('zk-proofs/range/', zk_views.zk_range, name='zk_range'),

    # API Endpoints
    path('api/blockchain/', include('blockchain.urls')),
    path('api/healthcare/', include('healthcare.urls')),
    path('api/cross-chain/', include('cross_chain.urls')),
    path('api/zk-proofs/', include('zk_proofs.urls')),
    path('api/v1/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
