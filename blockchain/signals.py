"""
MediChain Blockchain Signals
Django signals for blockchain events
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaction, RollupBatch


@receiver(post_save, sender=Transaction)
def handle_transaction_created(sender, instance, created, **kwargs):
    """Handle new transaction creation"""
    if created and instance.status == 'PENDING':
        # Auto-queue for rollup if batch threshold reached
        from blockchain.views import RollupViewSet
        pending_count = Transaction.objects.filter(status='PENDING').count()

        if pending_count >= 50:  # Batch threshold
            # Trigger rollup creation (would be Celery task in production)
            pass


@receiver(post_save, sender=RollupBatch)
def handle_batch_confirmed(sender, instance, created, **kwargs):
    """Handle rollup batch confirmation"""
    if not created and instance.status == 'CONFIRMED':
        # Update all transactions in batch
        instance.transactions.update(status='CONFIRMED')
