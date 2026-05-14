"""
MediChain Accounts App Configuration
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    verbose_name = 'MediChain Accounts'

    def ready(self):
        """Import signals when app is ready"""
        import accounts.signals
