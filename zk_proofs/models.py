from django.db import models
from django.utils import timezone


class ZKProofRecord(models.Model):
    PROOF_TYPES = [
        ('zk_snark', 'ZK-SNARK'),
        ('zk_stark', 'ZK-STARK'),
        ('range',    'Range Proof'),
    ]

    proof_type    = models.CharField(max_length=20, choices=PROOF_TYPES, default='zk_snark')
    inputs        = models.JSONField(default=list)
    public_output = models.CharField(max_length=500, blank=True)
    proof_payload = models.JSONField(default=dict)
    generated_by  = models.CharField(max_length=200)
    is_verified   = models.BooleanField(default=False)
    created_at    = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'zk_proof_records'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.proof_type} proof by {self.generated_by} at {self.created_at:%Y-%m-%d %H:%M}"
