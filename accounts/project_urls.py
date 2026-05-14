"""
MediChain Project Root URL Configuration
Add to your project's urls.py
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import login_view  # Import for default redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('healthcare/', include('healthcare.urls')),
    path('blockchain/', include('blockchain.urls')),
    path('api/v1/', include('healthcare.urls')),  # API endpoints
    path('', include('core.urls')),  # Index/dashboard views
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
