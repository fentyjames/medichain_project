"""
MediChain Database Router
Routes blockchain data to dedicated blockchain database
"""

class BlockchainRouter:
    """Router to control blockchain app database operations."""

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'blockchain':
            return 'blockchain'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'blockchain':
            return 'blockchain'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == 'blockchain' or obj2._meta.app_label == 'blockchain':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'blockchain':
            return db == 'blockchain'
        return db == 'default'
