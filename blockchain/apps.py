"""Blockchain app configuration"""
from django.apps import AppConfig

class BlockchainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blockchain'
    verbose_name = 'MediChain Blockchain'

    def ready(self):
        import blockchain.signals
