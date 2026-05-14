"""
MediChain Blockchain Models
Core blockchain data structures for Layer-2 rollup, cross-chain relay, and consensus
"""

import hashlib
import json
import time
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


def generate_uuid():
    return str(uuid.uuid4())

class BlockchainNetwork(models.Model):
    """Represents a blockchain network in the MediChain ecosystem"""
    network_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    chain_id = models.IntegerField()
    rpc_url = models.URLField()
    consensus_type = models.CharField(max_length=50, default='PBFT')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blockchain_networks'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (Chain ID: {self.chain_id})"


class Block(models.Model):
    """Represents a block in the MediChain blockchain"""
    block_number = models.BigIntegerField(unique=True)
    previous_hash = models.CharField(max_length=64)
    merkle_root = models.CharField(max_length=64)
    rollup_proof = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    nonce = models.BigIntegerField()
    hash = models.CharField(max_length=64, unique=True)
    network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE)
    transaction_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'blocks'
        ordering = ['-block_number']

    def calculate_hash(self):
        """Calculate SHA-256 hash of block contents"""
        block_string = json.dumps({
            'block_number': self.block_number,
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'rollup_proof': self.rollup_proof,
            'timestamp': str(self.timestamp),
            'nonce': self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def save(self, *args, **kwargs):
        if not self.hash:
            self.hash = self.calculate_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Block #{self.block_number} [{self.hash[:16]}...]"


class Transaction(models.Model):
    """Represents a transaction in the MediChain system"""
    TRANSACTION_TYPES = [
        ('CREATE', 'Record Creation'),
        ('UPDATE', 'Record Update'),
        ('SHARE', 'Record Sharing'),
        ('VERIFY', 'Record Verification'),
        ('ACCESS', 'Access Request'),
    ]

    tx_hash = models.CharField(max_length=64, unique=True)
    tx_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    sender = models.CharField(max_length=200)
    receiver = models.CharField(max_length=200, blank=True, null=True)
    data_hash = models.CharField(max_length=64)
    signature = models.TextField()
    #nonce = models.CharField(max_length=64, default=lambda: str(uuid.uuid4()))
    nonce = models.CharField(max_length=64, default=generate_uuid)
    timestamp = models.DateTimeField(auto_now_add=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, default='PENDING')
    gas_used = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'transactions'
        ordering = ['-timestamp']

    def calculate_hash(self):
        """Calculate transaction hash"""
        tx_string = json.dumps({
            'tx_type': self.tx_type,
            'sender': self.sender,
            'receiver': self.receiver,
            'data_hash': self.data_hash,
            'nonce': self.nonce,
            'timestamp': str(self.timestamp),
        }, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()

    def save(self, *args, **kwargs):
        if not self.tx_hash:
            self.tx_hash = self.calculate_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"TX-{self.tx_type}-{self.tx_hash[:16]}"


class RollupBatch(models.Model):
    """Layer-2 Rollup batch aggregation"""
    batch_id = models.CharField(max_length=64, unique=True)
    transactions = models.ManyToManyField(Transaction)
    merkle_root = models.CharField(max_length=64)
    zk_proof = models.TextField()
    proof_type = models.CharField(max_length=20, default='zk_snark')
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE)

    class Meta:
        db_table = 'rollup_batches'
        ordering = ['-created_at']

    def calculate_merkle_root(self):
        """Calculate Merkle root of batched transactions"""
        tx_hashes = sorted([tx.tx_hash for tx in self.transactions.all()])
        if not tx_hashes:
            return hashlib.sha256(b'empty').hexdigest()

        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])
            tx_hashes = [
                hashlib.sha256((tx_hashes[i] + tx_hashes[i+1]).encode()).hexdigest()
                for i in range(0, len(tx_hashes), 2)
            ]
        return tx_hashes[0]

    def save(self, *args, **kwargs):
        if not self.batch_id:
            self.batch_id = hashlib.sha256(
                f"batch_{time.time()}_{uuid.uuid4()}".encode()
            ).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"RollupBatch-{self.batch_id[:16]}"


class CrossChainMessage(models.Model):
    """Cross-chain relay messages"""
    message_id = models.CharField(max_length=64, unique=True)
    source_chain = models.ForeignKey(
        BlockchainNetwork, 
        on_delete=models.CASCADE, 
        related_name='source_messages'
    )
    target_chain = models.ForeignKey(
        BlockchainNetwork, 
        on_delete=models.CASCADE, 
        related_name='target_messages'
    )
    data_hash = models.CharField(max_length=64)
    proof = models.TextField()
    signature = models.TextField()
    nonce = models.CharField(max_length=64)
    status = models.CharField(max_length=20, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    relayed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'cross_chain_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"CCM-{self.source_chain.name}->{self.target_chain.name}"


class ValidatorNode(models.Model):
    """Validator nodes for consensus"""
    node_id = models.CharField(max_length=64, unique=True)
    public_key = models.TextField()
    stake_amount = models.DecimalField(max_digits=30, decimal_places=18, default=0)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE)

    class Meta:
        db_table = 'validator_nodes'

    def __str__(self):
        return f"Validator-{self.node_id[:16]}"


class SmartContract(models.Model):
    """Smart contracts deployed on MediChain"""
    contract_address = models.CharField(max_length=200, unique=True)
    contract_type = models.CharField(max_length=100)
    abi = models.JSONField()
    bytecode = models.TextField()
    deployed_at = models.DateTimeField(auto_now_add=True)
    network = models.ForeignKey(BlockchainNetwork, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'smart_contracts'

    def __str__(self):
        return f"Contract-{self.contract_type}-{self.contract_address[:16]}"
