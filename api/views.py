"""
MediChain API Views
Consolidated API endpoints for the MediChain framework
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Count, Q

from blockchain.models import (
    BlockchainNetwork, Block, Transaction, RollupBatch,
    CrossChainMessage, ValidatorNode
)
from healthcare.models import (
    Patient, Hospital, MedicalRecord, AccessPermission, AuditLog
)
from .serializers import (
    BlockchainNetworkSerializer, BlockSerializer, TransactionSerializer,
    RollupBatchSerializer, PatientSerializer, HospitalSerializer,
    MedicalRecordSerializer, DashboardStatsSerializer
)
from zk_proofs.zk_service import ZKProofService, MerkleTreeService
from cross_chain.relay_service import CrossChainRelayService


class AuthView(APIView):
    """Authentication endpoints"""

    def post(self, request):
        """Login and get token"""
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
            })
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


class DashboardView(APIView):
    """System dashboard statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = {
            'networks': BlockchainNetwork.objects.filter(is_active=True).count(),
            'total_blocks': Block.objects.count(),
            'total_transactions': Transaction.objects.count(),
            'pending_transactions': Transaction.objects.filter(status='PENDING').count(),
            'confirmed_transactions': Transaction.objects.filter(status='CONFIRMED').count(),
            'rollup_batches': RollupBatch.objects.count(),
            'pending_batches': RollupBatch.objects.filter(status='PENDING').count(),
            'validators': ValidatorNode.objects.filter(is_active=True).count(),
            'cross_chain_messages': CrossChainMessage.objects.count(),
            'patients': Patient.objects.filter(is_active=True).count(),
            'hospitals': Hospital.objects.filter(is_verified=True).count(),
            'medical_records': MedicalRecord.objects.filter(is_active=True).count(),
            'active_permissions': AccessPermission.objects.filter(is_active=True).count(),
        }
        serializer = DashboardStatsSerializer(data=stats)
        return Response(stats)


class NetworkStatusView(APIView):
    """Get network status and health"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        networks = BlockchainNetwork.objects.filter(is_active=True)
        data = []

        for network in networks:
            latest_block = Block.objects.filter(
                network=network
            ).order_by('-block_number').first()

            data.append({
                'network_id': network.network_id,
                'name': network.name,
                'chain_id': network.chain_id,
                'consensus': network.consensus_type,
                'latest_block': latest_block.block_number if latest_block else 0,
                'latest_block_hash': latest_block.hash[:16] + '...' if latest_block else None,
                'status': 'healthy',
            })

        return Response(data)


class CreateRollupView(APIView):
    """Create Layer-2 rollup batch"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        network_id = request.data.get('network_id')

        try:
            network = BlockchainNetwork.objects.get(network_id=network_id)
        except BlockchainNetwork.DoesNotExist:
            return Response(
                {'error': 'Network not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Get pending transactions
        pending_txs = Transaction.objects.filter(
            status='PENDING',
            block__isnull=True
        )[:50]

        if not pending_txs:
            return Response({
                'message': 'No pending transactions to batch',
                'batch_created': False
            })

        # Create batch
        batch = RollupBatch.objects.create(
            network=network,
            proof_type='zk_snark'
        )
        batch.transactions.set(pending_txs)
        batch.merkle_root = batch.calculate_merkle_root()

        # Generate ZK proof
        zk_service = ZKProofService()
        tx_hashes = [tx.tx_hash for tx in pending_txs]
        batch.zk_proof = zk_service.generate_proof(tx_hashes, batch.merkle_root)
        batch.save()

        pending_txs.update(status='BATCHED')

        return Response({
            'batch_id': batch.batch_id,
            'merkle_root': batch.merkle_root,
            'transaction_count': len(tx_hashes),
            'proof_type': batch.proof_type,
            'status': 'BATCHED',
            'batch_created': True,
        })


class SubmitRollupView(APIView):
    """Submit rollup batch to main chain"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        batch_id = request.data.get('batch_id')

        try:
            batch = RollupBatch.objects.get(batch_id=batch_id)
        except RollupBatch.DoesNotExist:
            return Response(
                {'error': 'Batch not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        if batch.status != 'BATCHED':
            return Response(
                {'error': f'Batch status is {batch.status}, expected BATCHED'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new block
        latest_block = Block.objects.filter(
            network=batch.network
        ).order_by('-block_number').first()

        new_block_number = (latest_block.block_number + 1) if latest_block else 1
        previous_hash = latest_block.hash if latest_block else '0' * 64

        block = Block.objects.create(
            block_number=new_block_number,
            previous_hash=previous_hash,
            merkle_root=batch.merkle_root,
            rollup_proof=batch.zk_proof,
            nonce=0,
            network=batch.network,
            transaction_count=batch.transactions.count()
        )

        # Update transactions
        batch.transactions.update(block=block, status='CONFIRMED')

        batch.status = 'CONFIRMED'
        batch.submitted_at = __import__('django.utils.timezone').utils.timezone.now()
        batch.save()

        return Response({
            'batch_id': batch.batch_id,
            'block_number': block.block_number,
            'block_hash': block.hash,
            'previous_hash': block.previous_hash,
            'transaction_count': block.transaction_count,
            'status': 'CONFIRMED',
        })


class CrossChainTransferView(APIView):
    """Cross-chain data transfer"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        source_id = request.data.get('source_chain')
        target_id = request.data.get('target_chain')
        data_hash = request.data.get('data_hash')
        proof = request.data.get('proof')
        sender = request.data.get('sender')

        try:
            source = BlockchainNetwork.objects.get(network_id=source_id)
            target = BlockchainNetwork.objects.get(network_id=target_id)
        except BlockchainNetwork.DoesNotExist:
            return Response(
                {'error': 'Source or target network not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        relay_service = CrossChainRelayService()

        # Create message
        message = relay_service.create_message(
            source_id, target_id, data_hash, proof, sender
        )

        # Relay message
        result = relay_service.relay_message(message)

        # Store in database
        CrossChainMessage.objects.create(
            message_id=message['message_id'],
            source_chain=source,
            target_chain=target,
            data_hash=data_hash,
            proof=proof,
            signature=message['signature'],
            nonce=message['nonce'],
            status=result['status']
        )

        return Response({
            'message_id': message['message_id'],
            'status': result['status'],
            'source_chain': source.name,
            'target_chain': target.name,
            'relayed_at': result.get('relayed_at'),
        })


class VerifyZKProofView(APIView):
    """Verify Zero-Knowledge Proof"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        proof = request.data.get('proof')
        public_output = request.data.get('public_output')
        expected_inputs = request.data.get('expected_inputs', [])
        proof_type = request.data.get('proof_type', 'zk_snark')

        zk_service = ZKProofService(proof_type)
        is_valid = zk_service.verify_proof(proof, public_output, expected_inputs)

        return Response({
            'is_valid': is_valid,
            'proof_type': proof_type,
            'public_output': public_output,
            'verification_time_ms': 50,  # Simulated
        })


class MerkleTreeView(APIView):
    """Merkle tree operations"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        action = request.data.get('action', 'build')

        if action == 'build':
            leaves = request.data.get('leaves', [])
            tree = MerkleTreeService.build_merkle_tree(leaves)
            return Response({
                'root': tree['root'],
                'leaf_count': tree['leaf_count'],
                'levels': len(tree['levels']),
            })

        elif action == 'verify':
            root = request.data.get('root')
            leaf = request.data.get('leaf')
            proof_path = request.data.get('proof_path', [])
            is_valid = MerkleTreeService.verify_merkle_proof(root, leaf, proof_path)
            return Response({'is_valid': is_valid})

        return Response(
            {'error': 'Invalid action'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class PatientRecordsView(APIView):
    """Get patient records with privacy controls"""
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(patient_id=patient_id)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        records = MedicalRecord.objects.filter(
            patient=patient,
            is_active=True
        )

        data = []
        for record in records:
            data.append({
                'record_id': record.record_id,
                'record_type': record.record_type,
                'title': record.title,
                'hospital': record.hospital.name,
                'data_hash': record.data_hash,
                'created_at': record.created_at,
                # Actual data not revealed - only hash
            })

        return Response({
            'patient_id': patient_id,
            'record_count': len(data),
            'records': data,
        })


class GrantAccessView(APIView):
    """Grant access to medical record"""
    permission_classes = [IsAuthenticated]

    def post(self, request, record_id):
        try:
            record = MedicalRecord.objects.get(record_id=record_id)
        except MedicalRecord.DoesNotExist:
            return Response(
                {'error': 'Record not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

        grantee = request.data.get('grantee')
        grantee_type = request.data.get('grantee_type', 'HOSPITAL')
        permission_type = request.data.get('permission_type', 'READ')
        purpose = request.data.get('purpose', 'Medical treatment')
        signature = request.data.get('signature', '')

        permission = AccessPermission.objects.create(
            record=record,
            grantor=record.patient,
            grantee=grantee,
            grantee_type=grantee_type,
            permission_type=permission_type,
            purpose=purpose,
            signature=signature,
        )

        # Log
        AuditLog.objects.create(
            log_id=f"audit_{record_id}_grant",
            record=record,
            actor=record.patient.patient_id,
            actor_type='PATIENT',
            action='SHARE',
            details={
                'grantee': grantee,
                'permission_type': permission_type,
                'purpose': purpose,
            }
        )

        return Response({
            'permission_id': permission.permission_id,
            'grantee': grantee,
            'permission_type': permission_type,
            'valid_from': permission.valid_from,
        })


class AuditTrailView(APIView):
    """Get audit trail for a record"""
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        logs = AuditLog.objects.filter(
            record__record_id=record_id
        ).order_by('-timestamp')[:100]

        data = [{
            'log_id': log.log_id,
            'action': log.action,
            'actor': log.actor,
            'actor_type': log.actor_type,
            'details': log.details,
            'timestamp': log.timestamp,
        } for log in logs]

        return Response({
            'record_id': record_id,
            'log_count': len(data),
            'logs': data,
        })
