"""
MediChain Blockchain Views
API endpoints + Template rendering for blockchain operations
"""

import hashlib
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import (
    BlockchainNetwork, Block, Transaction, RollupBatch,
    CrossChainMessage, ValidatorNode, SmartContract
)
from zk_proofs.zk_service import ZKProofService
from cross_chain.relay_service import CrossChainRelayService


# ==================== TEMPLATE VIEWS ====================

def index(request):
    """Main dashboard page"""
    from healthcare.models import Patient, Hospital, MedicalRecord, AuditLog
    stats = {
        'networks': BlockchainNetwork.objects.filter(is_active=True).count(),
        'total_blocks': Block.objects.count(),
        'total_transactions': Transaction.objects.count(),
        'pending_transactions': Transaction.objects.filter(status='PENDING').count(),
        'patients': Patient.objects.filter(is_active=True).count(),
        'hospitals': Hospital.objects.filter(is_verified=True).count(),
        'medical_records': MedicalRecord.objects.filter(is_active=True).count(),
    }
    recent_logs = AuditLog.objects.order_by('-timestamp')[:10]
    return render(request, 'index.html', {'stats': stats, 'recent_logs': recent_logs})


def blockchain_dashboard(request):
    """Blockchain explorer dashboard"""
    context = {
        'total_blocks': Block.objects.count(),
        'total_txs': Transaction.objects.count(),
        'pending_txs': Transaction.objects.filter(status='PENDING').count(),
        'validators': ValidatorNode.objects.filter(is_active=True).count(),
        'recent_blocks': Block.objects.order_by('-block_number')[:10],
        'networks': BlockchainNetwork.objects.filter(is_active=True),
    }
    return render(request, 'blockchain/dashboard.html', context)


def block_list(request):
    """List all blocks"""
    blocks = Block.objects.order_by('-block_number')
    return render(request, 'blockchain/block_list.html', {'blocks': blocks})


def transaction_list(request):
    """List all transactions"""
    transactions = Transaction.objects.order_by('-timestamp')
    return render(request, 'blockchain/transaction_list.html', {'transactions': transactions})


def transaction_add(request):
    """Create transaction form"""
    if request.method == 'POST':
        tx = Transaction.objects.create(
            tx_type=request.POST.get('tx_type', 'CREATE'),
            sender=request.POST.get('sender'),
            receiver=request.POST.get('receiver') or None,
            data_hash=request.POST.get('data_hash'),
            signature=request.POST.get('signature'),
            status='PENDING'
        )
        messages.success(request, f'Transaction created: {tx.tx_hash[:16]}...')
        return redirect('transaction_list')
    return render(request, 'blockchain/transaction_add.html')


def rollup_list(request):
    """List rollup batches"""
    rollups = RollupBatch.objects.order_by('-created_at')
    return render(request, 'blockchain/rollup_list.html', {'rollups': rollups})


def rollup_create(request):
    """Create rollup batch form"""
    if request.method == 'POST':
        network_id = request.POST.get('network_id')
        network = get_object_or_404(BlockchainNetwork, network_id=network_id)
        pending_txs = Transaction.objects.filter(status='PENDING', block__isnull=True)[:50]

        if not pending_txs:
            messages.warning(request, 'No pending transactions to batch')
            return redirect('rollup_list')

        batch = RollupBatch.objects.create(network=network, proof_type='zk_snark')
        batch.transactions.set(pending_txs)
        batch.merkle_root = batch.calculate_merkle_root()

        zk_service = ZKProofService()
        batch.zk_proof = zk_service.generate_proof(
            [tx.tx_hash for tx in pending_txs], batch.merkle_root
        )
        batch.save()
        pending_txs.update(status='BATCHED')

        messages.success(request, f'Rollup batch created: {batch.batch_id[:16]}...')
        return redirect('rollup_list')

    networks = BlockchainNetwork.objects.filter(is_active=True)
    return render(request, 'blockchain/rollup_create.html', {'networks': networks})


# ==================== API VIEWSETS ====================

class BlockchainNetworkViewSet(viewsets.ModelViewSet):
    queryset = BlockchainNetwork.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request):
        networks = BlockchainNetwork.objects.filter(is_active=True)
        data = [{
            'id': n.id, 'network_id': n.network_id, 'name': n.name,
            'chain_id': n.chain_id, 'rpc_url': n.rpc_url,
            'consensus_type': n.consensus_type,
        } for n in networks]
        return Response(data)


class BlockViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request):
        blocks = Block.objects.select_related('network').all()[:100]
        data = [{
            'block_number': b.block_number, 'hash': b.hash,
            'previous_hash': b.previous_hash, 'merkle_root': b.merkle_root,
            'transaction_count': b.transaction_count,
            'network': b.network.name, 'timestamp': b.timestamp,
        } for b in blocks]
        return Response(data)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request):
        tx_data = request.data
        transaction = Transaction.objects.create(
            tx_type=tx_data.get('tx_type', 'CREATE'),
            sender=tx_data.get('sender'),
            receiver=tx_data.get('receiver'),
            data_hash=tx_data.get('data_hash'),
            signature=tx_data.get('signature'),
            status='PENDING'
        )
        return Response({
            'tx_hash': transaction.tx_hash,
            'status': transaction.status,
            'message': 'Transaction created and queued for rollup'
        }, status=201)


class RollupViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def create_batch(self, request):
        network_id = request.data.get('network_id')
        network = get_object_or_404(BlockchainNetwork, network_id=network_id)
        pending_txs = Transaction.objects.filter(status='PENDING', block__isnull=True)[:50]

        if not pending_txs:
            return Response({'message': 'No pending transactions'}, status=200)

        batch = RollupBatch.objects.create(network=network, proof_type='zk_snark')
        batch.transactions.set(pending_txs)
        batch.merkle_root = batch.calculate_merkle_root()

        zk_service = ZKProofService()
        batch.zk_proof = zk_service.generate_proof(
            [tx.tx_hash for tx in pending_txs], batch.merkle_root
        )
        batch.save()
        pending_txs.update(status='BATCHED')

        return Response({
            'batch_id': batch.batch_id, 'merkle_root': batch.merkle_root,
            'tx_count': pending_txs.count(), 'proof_type': batch.proof_type,
            'status': 'BATCHED',
        })


class ConsensusViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from healthcare.models import Patient, Hospital, MedicalRecord
        stats = {
            'networks': BlockchainNetwork.objects.filter(is_active=True).count(),
            'total_blocks': Block.objects.count(),
            'total_transactions': Transaction.objects.count(),
            'pending_transactions': Transaction.objects.filter(status='PENDING').count(),
            'rollup_batches': RollupBatch.objects.count(),
            'validators': ValidatorNode.objects.filter(is_active=True).count(),
            'cross_chain_messages': CrossChainMessage.objects.count(),
            'patients': Patient.objects.filter(is_active=True).count(),
            'hospitals': Hospital.objects.filter(is_verified=True).count(),
            'medical_records': MedicalRecord.objects.filter(is_active=True).count(),
        }
        return Response(stats)
