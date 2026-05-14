"""MediChain URL Configuration"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts import views as accounts_views
from blockchain.urls import template_urlpatterns as blockchain_templates
from cross_chain.urls import template_urlpatterns as cross_chain_templates
from healthcare.urls import template_urlpatterns as healthcare_templates
from zk_proofs.urls import template_urlpatterns as zk_templates

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # ==================== PUBLIC PAGES ====================
    path('', accounts_views.landing, name='landing'),
    path('dashboard/', accounts_views.index, name='index'),
    path('about/', accounts_views.about, name='about'),

    # Accounts
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # App template views — defined in each app's urls.py
    path('blockchain/', include(blockchain_templates)),
    path('healthcare/', include(healthcare_templates)),
    path('cross-chain/', include(cross_chain_templates)),
    path('zk-proofs/', include(zk_templates)),

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
