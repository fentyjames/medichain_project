"""
MediChain Cross-Chain Views
Template rendering + API for cross-chain relay
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from blockchain.models import BlockchainNetwork, CrossChainMessage
from .relay_service import CrossChainRelayService


# ==================== TEMPLATE VIEWS ====================

def crosschain_dashboard(request):
    """Cross-chain dashboard"""
    messages_list = CrossChainMessage.objects.order_by('-created_at')
    context = {
        'total_messages': messages_list.count(),
        'relayed': messages_list.filter(status='RELAYED').count(),
        'pending': messages_list.filter(status='PENDING').count(),
        'rejected': messages_list.filter(status='REJECTED').count(),
        'messages': messages_list[:20],
    }
    return render(request, 'cross_chain/dashboard.html', context)


def crosschain_transfer(request):
    """Cross-chain transfer form"""
    if request.method == 'POST':
        source = get_object_or_404(BlockchainNetwork, network_id=request.POST.get('source_chain'))
        target = get_object_or_404(BlockchainNetwork, network_id=request.POST.get('target_chain'))

        relay_service = CrossChainRelayService()
        message = relay_service.create_message(
            request.POST.get('source_chain'),
            request.POST.get('target_chain'),
            request.POST.get('data_hash'),
            request.POST.get('proof'),
            request.POST.get('sender')
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
            status=result['status']
        )

        messages.success(request, f'Message relayed: {message["message_id"][:16]}...')
        return redirect('crosschain_dashboard')

    networks = BlockchainNetwork.objects.filter(is_active=True)
    return render(request, 'cross_chain/transfer.html', {'networks': networks})


def crosschain_detail(request, message_id):
    """Message detail"""
    msg = get_object_or_404(CrossChainMessage, message_id=message_id)
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
            signature=message['signature'],
            nonce=message['nonce'],
            status=result['status']
        )

        return Response({
            'message_id': message['message_id'],
            'status': result['status'],
            'source_chain': source.name,
            'target_chain': target.name,
        })


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
        status = relay_service.get_relay_status(message_id)
        if status:
            return Response(status)
        return Response({'error': 'Message not found'}, status=404)


class BridgeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        relay_service = CrossChainRelayService()
        return Response(relay_service.get_bridge_stats())
