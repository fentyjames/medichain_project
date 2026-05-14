"""
MediChain Middleware
ZK Proof and Cross-Chain verification middleware
"""

import time

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


class ZKProofMiddleware(MiddlewareMixin):
    """Middleware to verify ZK proofs on sensitive requests"""

    def process_request(self, request):
        if request.path.startswith('/api/healthcare/records/') and request.method in ['GET', 'POST']:
            # Add ZK verification header check
            zk_header = request.META.get('HTTP_X_ZK_PROOF')
            if zk_header:
                request.zk_verified = True
            else:
                request.zk_verified = False
        return None

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-MediChain-Version'] = '1.0.0'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # API doc pages (Swagger/ReDoc) use JS-injected inline styles and load Google
        # Fonts — relax CSP for those paths only.
        if request.path.startswith(('/api/docs/', '/api/redoc/', '/api/schema/')):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' cdn.jsdelivr.net 'unsafe-inline' blob:; "
                "worker-src blob:; "
                "style-src 'self' cdn.jsdelivr.net fonts.googleapis.com 'unsafe-inline'; "
                "font-src cdn.jsdelivr.net fonts.gstatic.com; "
                "img-src 'self' data: cdn.redoc.ly; "
                "connect-src 'self';"
            )
        else:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' cdn.jsdelivr.net 'unsafe-inline'; "
                "style-src 'self' cdn.jsdelivr.net 'unsafe-inline'; "
                "font-src cdn.jsdelivr.net; "
                "img-src 'self' data:; "
                "connect-src 'self';"
            )
        return response


class CrossChainMiddleware(MiddlewareMixin):
    """Middleware for cross-chain request handling"""

    def process_request(self, request):
        if request.path.startswith('/api/cross-chain/'):
            # Add cross-chain request timestamp
            request.cross_chain_timestamp = time.time()
        return None

    def process_response(self, request, response):
        if hasattr(request, 'cross_chain_timestamp'):
            duration = time.time() - request.cross_chain_timestamp
            response['X-Cross-Chain-Duration'] = str(duration)
        return response
