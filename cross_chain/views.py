"""
MediChain Cross-Chain Views
Template rendering + API for cross-chain relay
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from blockchain.models import BlockchainNetwork, CrossChainMessage

from .relay_service import CrossChainRelayService


def _paginate(request, qs, per_page=20):
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    params = request.GET.copy()
    params.pop('page', None)
    qs_str = ('?' + params.urlencode() + '&') if params.urlencode() else '?'
    return page_obj, qs_str


# ==================== TEMPLATE VIEWS ====================

@login_required(login_url='/accounts/login/')
def crosschain_dashboard(request):
    """Cross-chain dashboard with status filter and pagination."""
    status_filter = request.GET.get('status', '').strip()
    qs = CrossChainMessage.objects.select_related('source_chain', 'target_chain').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)

    total_messages = CrossChainMessage.objects.count()
    relayed = CrossChainMessage.objects.filter(status='RELAYED').count()
    pending = CrossChainMessage.objects.filter(status='PENDING').count()
    verified = CrossChainMessage.objects.filter(status='VERIFIED').count()
    rejected = CrossChainMessage.objects.filter(status='FAILED').count()

    page_obj, qs_str = _paginate(request, qs, 20)
    return render(request, 'cross_chain/dashboard.html', {
        'total_messages': total_messages,
        'relayed': relayed,
        'pending': pending,
        'verified': verified,
        'rejected': rejected,
        'messages': page_obj,
        'page_obj': page_obj,
        'query_string': qs_str,
        'selected_status': status_filter,
    })


@login_required(login_url='/accounts/login/')
def crosschain_transfer(request):
    """Cross-chain transfer form."""
    if request.method == 'POST':
        source = get_object_or_404(BlockchainNetwork, network_id=request.POST.get('source_chain'))
        target = get_object_or_404(BlockchainNetwork, network_id=request.POST.get('target_chain'))

        relay_service = CrossChainRelayService()
        message = relay_service.create_message(
            request.POST.get('source_chain'),
            request.POST.get('target_chain'),
            request.POST.get('data_hash'),
            request.POST.get('proof'),
            request.POST.get('sender'),
        )
        result = relay_service.relay_message(message)

        CrossChainMessage.objects.create(
            message_id=message['message_id'],
            source_chain=source,
            target_chain=target,
            data_hash=request.POST.get('data_hash'),
            proof=request.POST.get('proof'),
            signature=message['signature'],
            nonce=message['nonce'],
            status=result['status'],
        )

        messages.success(request, f'Message relayed: {message["message_id"][:16]}... — Status: {result["status"]}')
        return redirect('crosschain_dashboard')

    networks = BlockchainNetwork.objects.filter(is_active=True)
    return render(request, 'cross_chain/transfer.html', {'networks': networks})


@login_required(login_url='/accounts/login/')
def crosschain_detail(request, message_id):
    """Message detail."""
    msg = get_object_or_404(
        CrossChainMessage.objects.select_related('source_chain', 'target_chain'),
        message_id=message_id,
    )
    return render(request, 'cross_chain/detail.html', {'message': msg})


# ==================== API VIEWS ====================

class RelayMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        source_id = request.data.get('source_chain')
        target_id = request.data.get('target_chain')
        data_hash = request.data.get('data_hash')
        proof = request.data.get('proof')
        sender = request.data.get('sender')

        source = get_object_or_404(BlockchainNetwork, network_id=source_id)
        target = get_object_or_404(BlockchainNetwork, network_id=target_id)

        relay_service = CrossChainRelayService()
        message = relay_service.create_message(source_id, target_id, data_hash, proof, sender)
        result = relay_service.relay_message(message)

        CrossChainMessage.objects.create(
            message_id=message['message_id'],
            source_chain=source, target_chain=target,
            data_hash=data_hash, proof=proof,
            signature=message['signature'], nonce=message['nonce'],
            status=result['status'],
        )

        return Response({'message_id': message['message_id'], 'status': result['status'], 'source_chain': source.name, 'target_chain': target.name})


class VerifyMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = request.data.get('message', {})
        relay_service = CrossChainRelayService()
        is_valid = relay_service.verify_message(message)
        return Response({'is_valid': is_valid, 'message_id': message.get('message_id')})


class RelayStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, message_id):
        relay_service = CrossChainRelayService()
        status_data = relay_service.get_relay_status(message_id)
        if status_data:
            return Response(status_data)
        return Response({'error': 'Message not found'}, status=404)


class BridgeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        relay_service = CrossChainRelayService()
        return Response(relay_service.get_bridge_stats())
