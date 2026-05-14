"""Blockchain admin configuration"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Block, BlockchainNetwork, CrossChainMessage, RollupBatch, SmartContract, Transaction, ValidatorNode


def short(value, length=16):
    """Truncate a long hash/ID for list display."""
    if not value:
        return '-'
    return f"{value[:length]}…" if len(value) > length else value


def _badge(label, color, text_color='#000'):
    return format_html(
        '<span style="background:{};color:{};padding:2px 10px;border-radius:6px;'
        'font-size:0.75rem;font-weight:600;">{}</span>',
        color, text_color, label,
    )


# ==================== BLOCKCHAIN NETWORK ====================

@admin.register(BlockchainNetwork)
class BlockchainNetworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'network_id', 'chain_id', 'consensus_type', 'rpc_url', 'active_badge', 'created_at']
    list_filter = ['is_active', 'consensus_type']
    search_fields = ['name', 'network_id']
    readonly_fields = ['created_at']
    ordering = ['name']

    def active_badge(self, obj):
        return _badge('Active', '#22c55e') if obj.is_active else _badge('Inactive', '#64748b', '#fff')
    active_badge.short_description = 'Status'


# ==================== BLOCK ====================

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['block_number', 'short_hash', 'network', 'transaction_count', 'short_merkle_root', 'timestamp']
    list_filter = ['network']
    search_fields = ['hash', 'merkle_root']
    readonly_fields = ['hash', 'timestamp']
    ordering = ['-block_number']
    date_hierarchy = 'timestamp'

    def short_hash(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.hash))
    short_hash.short_description = 'Hash'

    def short_merkle_root(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.merkle_root))
    short_merkle_root.short_description = 'Merkle Root'


# ==================== TRANSACTION ====================

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['short_tx_hash', 'type_badge', 'sender', 'receiver', 'status_badge', 'block', 'gas_used', 'timestamp']
    list_filter = ['tx_type', 'status']
    search_fields = ['tx_hash', 'sender', 'receiver']
    readonly_fields = ['tx_hash', 'timestamp']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'

    def short_tx_hash(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.tx_hash))
    short_tx_hash.short_description = 'TX Hash'

    def type_badge(self, obj):
        colors = {
            'CREATE': '#38bdf8',
            'UPDATE': '#facc15',
            'SHARE':  '#a78bfa',
            'VERIFY': '#22c55e',
            'ACCESS': '#fb923c',
        }
        return _badge(obj.get_tx_type_display(), colors.get(obj.tx_type, '#94a3b8'))
    type_badge.short_description = 'Type'

    def status_badge(self, obj):
        colors = {
            'PENDING':   '#facc15',
            'BATCHED':   '#38bdf8',
            'CONFIRMED': '#22c55e',
            'FAILED':    '#f87171',
        }
        return _badge(obj.status, colors.get(obj.status, '#94a3b8'))
    status_badge.short_description = 'Status'


# ==================== ROLLUP BATCH ====================

@admin.register(RollupBatch)
class RollupBatchAdmin(admin.ModelAdmin):
    list_display = ['short_batch_id', 'network', 'proof_type', 'tx_count', 'status_badge', 'created_at', 'submitted_at']
    list_filter = ['status', 'proof_type', 'network']
    readonly_fields = ['batch_id', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def short_batch_id(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.batch_id))
    short_batch_id.short_description = 'Batch ID'

    def tx_count(self, obj):
        return obj.transactions.count()
    tx_count.short_description = '# Transactions'

    def status_badge(self, obj):
        colors = {
            'PENDING':   '#facc15',
            'BATCHED':   '#38bdf8',
            'CONFIRMED': '#22c55e',
            'FAILED':    '#f87171',
        }
        return _badge(obj.status, colors.get(obj.status, '#94a3b8'))
    status_badge.short_description = 'Status'


# ==================== CROSS-CHAIN MESSAGE ====================

@admin.register(CrossChainMessage)
class CrossChainMessageAdmin(admin.ModelAdmin):
    list_display = ['short_message_id', 'source_chain', 'target_chain', 'status_badge', 'created_at', 'relayed_at', 'verified_at']
    list_filter = ['status', 'source_chain', 'target_chain']
    search_fields = ['message_id', 'data_hash']
    readonly_fields = ['message_id', 'created_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    def short_message_id(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.message_id))
    short_message_id.short_description = 'Message ID'

    def status_badge(self, obj):
        colors = {
            'PENDING':  '#facc15',
            'RELAYED':  '#38bdf8',
            'VERIFIED': '#22c55e',
            'FAILED':   '#f87171',
        }
        return _badge(obj.status, colors.get(obj.status, '#94a3b8'))
    status_badge.short_description = 'Status'


# ==================== VALIDATOR NODE ====================

@admin.register(ValidatorNode)
class ValidatorNodeAdmin(admin.ModelAdmin):
    list_display = ['short_node_id', 'network', 'stake_amount', 'active_badge', 'last_seen']
    list_filter = ['is_active', 'network']
    search_fields = ['node_id']
    readonly_fields = ['last_seen']

    def short_node_id(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.node_id))
    short_node_id.short_description = 'Node ID'

    def active_badge(self, obj):
        return _badge('Active', '#22c55e') if obj.is_active else _badge('Offline', '#64748b', '#fff')
    active_badge.short_description = 'Status'


# ==================== SMART CONTRACT ====================

@admin.register(SmartContract)
class SmartContractAdmin(admin.ModelAdmin):
    list_display = ['short_address', 'contract_type', 'network', 'active_badge', 'deployed_at']
    list_filter = ['is_active', 'contract_type', 'network']
    search_fields = ['contract_address', 'contract_type']
    readonly_fields = ['deployed_at']
    date_hierarchy = 'deployed_at'

    def short_address(self, obj):
        return format_html('<code style="font-size:0.8rem;">{}</code>', short(obj.contract_address))
    short_address.short_description = 'Address'

    def active_badge(self, obj):
        return _badge('Active', '#22c55e') if obj.is_active else _badge('Inactive', '#64748b', '#fff')
    active_badge.short_description = 'Status'
