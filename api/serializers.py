"""
MediChain API Serializers
Data serialization for REST API endpoints
"""

from rest_framework import serializers
from blockchain.models import (
    BlockchainNetwork, Block, Transaction, RollupBatch,
    CrossChainMessage, ValidatorNode
)
from healthcare.models import (
    Patient, Hospital, MedicalRecord, AccessPermission, AuditLog
)


class BlockchainNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlockchainNetwork
        fields = ['id', 'network_id', 'name', 'chain_id', 'consensus_type', 'is_active']


class BlockSerializer(serializers.ModelSerializer):
    network_name = serializers.CharField(source='network.name', read_only=True)

    class Meta:
        model = Block
        fields = ['block_number', 'hash', 'previous_hash', 'merkle_root', 
                   'transaction_count', 'network_name', 'timestamp']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['tx_hash', 'tx_type', 'sender', 'receiver', 
                 'data_hash', 'status', 'timestamp']


class RollupBatchSerializer(serializers.ModelSerializer):
    transaction_count = serializers.IntegerField(source='transactions.count', read_only=True)
    network_name = serializers.CharField(source='network.name', read_only=True)

    class Meta:
        model = RollupBatch
        fields = ['batch_id', 'merkle_root', 'proof_type', 'status',
                 'transaction_count', 'network_name', 'created_at']


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['patient_id', 'public_key', 'blood_type', 'allergies', 'created_at']


class HospitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = ['hospital_id', 'name', 'address', 'license_number', 'is_verified']


class MedicalRecordSerializer(serializers.ModelSerializer):
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    hospital_name = serializers.CharField(source='hospital.name', read_only=True)

    class Meta:
        model = MedicalRecord
        fields = ['record_id', 'record_type', 'title', 'description',
                 'patient_id', 'hospital_name', 'data_hash', 'ipfs_hash',
                 'created_at']


class AccessPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessPermission
        fields = ['permission_id', 'grantee', 'grantee_type', 
                 'permission_type', 'purpose', 'valid_from', 'valid_until']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['log_id', 'actor', 'action', 'details', 'timestamp']


class DashboardStatsSerializer(serializers.Serializer):
    networks = serializers.IntegerField()
    total_blocks = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    pending_transactions = serializers.IntegerField()
    rollup_batches = serializers.IntegerField()
    validators = serializers.IntegerField()
    cross_chain_messages = serializers.IntegerField()
