"""Blockchain admin configuration"""
from django.contrib import admin
from .models import (
    BlockchainNetwork, Block, Transaction, RollupBatch,
    CrossChainMessage, ValidatorNode, SmartContract
)

@admin.register(BlockchainNetwork)
class BlockchainNetworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'chain_id', 'consensus_type', 'is_active']
    list_filter = ['is_active', 'consensus_type']

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['block_number', 'hash', 'network', 'transaction_count', 'timestamp']
    list_filter = ['network']
    ordering = ['-block_number']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['tx_hash', 'tx_type', 'sender', 'status', 'timestamp']
    list_filter = ['tx_type', 'status']
    search_fields = ['tx_hash', 'sender']

@admin.register(RollupBatch)
class RollupBatchAdmin(admin.ModelAdmin):
    list_display = ['batch_id', 'network', 'status', 'created_at']
    list_filter = ['status', 'network']

@admin.register(CrossChainMessage)
class CrossChainMessageAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'source_chain', 'target_chain', 'status']
    list_filter = ['status']

@admin.register(ValidatorNode)
class ValidatorNodeAdmin(admin.ModelAdmin):
    list_display = ['node_id', 'network', 'stake_amount', 'is_active']
    list_filter = ['is_active', 'network']
