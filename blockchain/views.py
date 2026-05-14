"""
MediChain Blockchain Views
API endpoints + Template rendering for blockchain operations
"""

import hashlib
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cross_chain.relay_service import CrossChainRelayService
from zk_proofs.zk_service import ZKProofService

from .models import Block, BlockchainNetwork, CrossChainMessage, RollupBatch, SmartContract, Transaction, ValidatorNode


def _paginate(request, qs, per_page=25):
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    params = request.GET.copy()
    params.pop('page', None)
    qs_str = ('?' + params.urlencode() + '&') if params.urlencode() else '?'
    return page_obj, qs_str


# ==================== TEMPLATE VIEWS ====================

def index(request):
    """Main dashboard page (no login guard — mounted at root)"""
    from healthcare.models import AuditLog, Hospital, MedicalRecord, Patient
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


@login_required(login_url='/accounts/login/')
def blockchain_dashboard(request):
    """Blockchain explorer dashboard."""
    context = {
        'total_blocks': Block.objects.count(),
        'total_txs': Transaction.objects.count(),
        'pending_txs': Transaction.objects.filter(status='PENDING').count(),
        'validators': ValidatorNode.objects.filter(is_active=True).count(),
        'recent_blocks': Block.objects.select_related('network').order_by('-block_number')[:10],
        'networks': BlockchainNetwork.objects.filter(is_active=True),
    }
    return render(request, 'blockchain/dashboard.html', context)


@login_required(login_url='/accounts/login/')
def block_list(request):
    """List all blocks with pagination."""
    qs = Block.objects.select_related('network').order_by('-block_number')
    page_obj, qs_str = _paginate(request, qs, 25)
    return render(request, 'blockchain/block_list.html', {
        'blocks': page_obj,
        'page_obj': page_obj,
        'query_string': qs_str,
    })


@login_required(login_url='/accounts/login/')
def transaction_list(request):
    """List all transactions with search + type/status filters."""
    q = request.GET.get('q', '').strip()
    tx_type = request.GET.get('type', '').strip()
    tx_status = request.GET.get('status', '').strip()

    qs = Transaction.objects.select_related('block').order_by('-timestamp')
    if q:
        qs = qs.filter(Q(tx_hash__icontains=q) | Q(sender__icontains=q) | Q(receiver__icontains=q))
    if tx_type:
        qs = qs.filter(tx_type=tx_type)
    if tx_status:
        qs = qs.filter(status=tx_status)

    page_obj, qs_str = _paginate(request, qs, 25)
    return render(request, 'blockchain/transaction_list.html', {
        'transactions': page_obj,
        'page_obj': page_obj,
        'query_string': qs_str,
        'q': q,
        'selected_type': tx_type,
        'selected_status': tx_status,
    })


@login_required(login_url='/accounts/login/')
def transaction_add(request):
    """Create transaction form."""
    if request.method == 'POST':
        tx = Transaction.objects.create(
            tx_type=request.POST.get('tx_type', 'CREATE'),
            sender=request.POST.get('sender'),
            receiver=request.POST.get('receiver') or None,
            data_hash=request.POST.get('data_hash'),
            signature=request.POST.get('signature'),
            status='PENDING',
        )
        messages.success(request, f'Transaction created: {tx.tx_hash[:16]}...')
        return redirect('transaction_list')
    return render(request, 'blockchain/transaction_add.html')


@login_required(login_url='/accounts/login/')
def rollup_list(request):
    """List rollup batches with pagination."""
    qs = RollupBatch.objects.select_related('network').order_by('-created_at')
    page_obj, qs_str = _paginate(request, qs, 12)
    return render(request, 'blockchain/rollup_list.html', {
        'rollups': page_obj,
        'page_obj': page_obj,
        'query_string': qs_str,
    })


@login_required(login_url='/accounts/login/')
def rollup_create(request):
    """Create rollup batch form."""
    if request.method == 'POST':
        network_id = request.POST.get('network_id')
        network = get_object_or_404(BlockchainNetwork, network_id=network_id)
        pending_txs = list(Transaction.objects.filter(status='PENDING', block__isnull=True)[:50])

        if not pending_txs:
            messages.warning(request, 'No pending transactions to batch')
            return redirect('rollup_list')

        tx_ids = [tx.pk for tx in pending_txs]
        batch = RollupBatch.objects.create(network=network, proof_type='zk_snark', merkle_root='')
        batch.transactions.set(pending_txs)
        batch.merkle_root = batch.calculate_merkle_root()

        zk_service = ZKProofService()
        batch.zk_proof = zk_service.generate_proof([tx.tx_hash for tx in pending_txs], batch.merkle_root)
        batch.status = 'BATCHED'
        batch.save()

        Transaction.objects.filter(pk__in=tx_ids).update(status='BATCHED')
        messages.success(request, f'Rollup batch created: {batch.batch_id[:16]}... ({len(tx_ids)} TXs)')
        return redirect('rollup_list')

    networks = BlockchainNetwork.objects.filter(is_active=True)
    pending_count = Transaction.objects.filter(status='PENDING', block__isnull=True).count()
    return render(request, 'blockchain/rollup_create.html', {
        'networks': networks,
        'pending_count': pending_count,
    })


# ==================== DETAIL VIEWS ====================

@login_required(login_url='/accounts/login/')
def block_detail(request, block_number):
    block = get_object_or_404(Block.objects.select_related('network'), block_number=block_number)
    transactions = Transaction.objects.filter(block=block).order_by('-timestamp')
    return render(request, 'blockchain/block_detail.html', {
        'block': block, 'transactions': transactions,
    })


@login_required(login_url='/accounts/login/')
def transaction_detail(request, tx_hash):
    tx = get_object_or_404(Transaction.objects.select_related('block__network'), tx_hash=tx_hash)
    return render(request, 'blockchain/transaction_detail.html', {'tx': tx})


@login_required(login_url='/accounts/login/')
def rollup_detail(request, batch_id):
    batch = get_object_or_404(RollupBatch.objects.select_related('network'), batch_id=batch_id)
    transactions = batch.transactions.all().order_by('-timestamp')
    return render(request, 'blockchain/rollup_detail.html', {
        'batch': batch, 'transactions': transactions,
    })


# ==================== API VIEWSETS ====================

class BlockchainNetworkViewSet(viewsets.ModelViewSet):
    queryset = BlockchainNetwork.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request):
        networks = BlockchainNetwork.objects.filter(is_active=True)
        data = [{'id': n.id, 'network_id': n.network_id, 'name': n.name, 'chain_id': n.chain_id, 'rpc_url': n.rpc_url, 'consensus_type': n.consensus_type} for n in networks]
        return Response(data)


class BlockViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    permission_classes = [IsAuthenticated]

    def list(self, request):
        blocks = Block.objects.select_related('network').all()[:100]
        data = [{'block_number': b.block_number, 'hash': b.hash, 'previous_hash': b.previous_hash, 'merkle_root': b.merkle_root, 'transaction_count': b.transaction_count, 'network': b.network.name, 'timestamp': b.timestamp} for b in blocks]
        return Response(data)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request):
        tx_data = request.data
        transaction = Transaction.objects.create(
            tx_type=tx_data.get('tx_type', 'CREATE'), sender=tx_data.get('sender'),
            receiver=tx_data.get('receiver'), data_hash=tx_data.get('data_hash'),
            signature=tx_data.get('signature'), status='PENDING',
        )
        return Response({'tx_hash': transaction.tx_hash, 'status': transaction.status, 'message': 'Transaction created and queued for rollup'}, status=201)


class RollupViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def create_batch(self, request):
        network_id = request.data.get('network_id')
        network = get_object_or_404(BlockchainNetwork, network_id=network_id)
        pending_txs = list(Transaction.objects.filter(status='PENDING', block__isnull=True)[:50])

        if not pending_txs:
            return Response({'message': 'No pending transactions'}, status=200)

        tx_ids = [tx.pk for tx in pending_txs]
        batch = RollupBatch.objects.create(network=network, proof_type='zk_snark', merkle_root='')
        batch.transactions.set(pending_txs)
        batch.merkle_root = batch.calculate_merkle_root()

        zk_service = ZKProofService()
        batch.zk_proof = zk_service.generate_proof([tx.tx_hash for tx in pending_txs], batch.merkle_root)
        batch.save()
        Transaction.objects.filter(pk__in=tx_ids).update(status='BATCHED')

        return Response({'batch_id': batch.batch_id, 'merkle_root': batch.merkle_root, 'tx_count': len(tx_ids), 'proof_type': batch.proof_type, 'status': 'BATCHED'})


class ConsensusViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from healthcare.models import Hospital, MedicalRecord, Patient
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
