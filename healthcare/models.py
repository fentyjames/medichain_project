"""
MediChain Healthcare Models
Patient records, access control, and medical data management
"""

import hashlib
import json
import uuid

from django.apps import apps  # Add this at top
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone


class Patient(models.Model):
    """Patient entity in MediChain"""
    patient_id = models.CharField(max_length=64, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    public_key = models.TextField()
    date_of_birth = models.DateField(null=True, blank=True)
    blood_type = models.CharField(max_length=10, blank=True)
    allergies = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'patients'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Auto-generate patient_id if missing"""
        if not self.patient_id:
            self.patient_id = hashlib.sha256(
                f"patient_{uuid.uuid4()}_{timezone.now().timestamp()}".encode()
            ).hexdigest()
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Patient-{self.patient_id[:16]}"


class Hospital(models.Model):
    """Hospital entity"""
    hospital_id = models.CharField(max_length=64, unique=True,
                                   validators=[MinLengthValidator(1)] ) # Prevents empty strings
    name = models.CharField(max_length=200)
    address = models.TextField()
    license_number = models.CharField(max_length=100)
    public_key = models.TextField()
    # Use string reference instead of direct import
    blockchain_network = models.ForeignKey(
        'blockchain.BlockchainNetwork',  # String reference: 'app_name.ModelName'
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    # blockchain_network_id = models.CharField(
    #     max_length=100,
    #     null=True,
    #     blank=True,
    #     help_text="ID of the network in the blockchain database"
    # )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hospitals'

    def save(self, *args, **kwargs):
        if not self.hospital_id:
            self.hospital_id = hashlib.sha256(
                f"hospital_{uuid.uuid4()}_{timezone.now().timestamp()}".encode()
            ).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Hospital-{self.name}"


class Laboratory(models.Model):
    """Laboratory entity"""
    lab_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    accreditation = models.CharField(max_length=100)
    public_key = models.TextField()
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        db_table = 'laboratories'

    def __str__(self):
        return f"Lab-{self.name}"


class InsuranceProvider(models.Model):
    """Insurance provider entity"""
    provider_id = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100)
    public_key = models.TextField()

    class Meta:
        db_table = 'insurance_providers'

    def __str__(self):
        return f"Insurance-{self.name}"


class MedicalRecord(models.Model):
    """Medical record with off-chain storage and on-chain hash"""
    RECORD_TYPES = [
        ('DIAGNOSIS', 'Diagnosis'),
        ('LAB_RESULT', 'Laboratory Result'),
        ('PRESCRIPTION', 'Prescription'),
        ('IMAGING', 'Medical Imaging'),
        ('SURGERY', 'Surgery Report'),
        ('DISCHARGE', 'Discharge Summary'),
        ('INSURANCE', 'Insurance Claim'),
    ]

    record_id = models.CharField(max_length=64, unique=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    record_type = models.CharField(max_length=20, choices=RECORD_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField()

    # Off-chain storage references
    ipfs_hash = models.CharField(max_length=64, blank=True)
    file_size = models.BigIntegerField(default=0)
    encryption_key_hash = models.CharField(max_length=64, blank=True)

    # On-chain anchor
    data_hash = models.CharField(max_length=64)
    metadata_hash = models.CharField(max_length=64)

    # Blockchain reference
    blockchain_tx = models.ForeignKey(
        'blockchain.Transaction',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    # blockchain_tx_hash = models.CharField(
    # max_length=64,
    # null=True,
    # blank=True,
    # db_index=True,
    # help_text="Transaction hash from blockchain database"
    # )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'medical_records'
        ordering = ['-created_at']

    def calculate_hash(self):
        """Calculate hash of record metadata"""
        # created_at is excluded: it's auto_now_add and is None before the first
        # super().save(), so including it makes the hash non-idempotent.
        record_data = {
            'record_id': self.record_id,
            'patient': self.patient.patient_id,
            'hospital': self.hospital.hospital_id,
            'record_type': self.record_type,
            'title': self.title,
            'description': self.description,
        }
        return hashlib.sha256(
            json.dumps(record_data, sort_keys=True).encode()
        ).hexdigest()

    def save(self, *args, **kwargs):
        if not self.record_id:
            self.record_id = hashlib.sha256(
                f"record_{uuid.uuid4()}_{timezone.now().timestamp()}".encode()
            ).hexdigest()
        if not self.data_hash:
            self.data_hash = self.calculate_hash()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Record-{self.record_type}-{self.record_id[:16]}"


class AccessPermission(models.Model):
    """Access control for medical records"""
    PERMISSION_TYPES = [
        ('READ', 'Read Only'),
        ('WRITE', 'Read and Write'),
        ('SHARE', 'Share with Others'),
    ]

    permission_id = models.CharField(max_length=64, unique=True)
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE)
    grantor = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='granted_permissions'
    )
    grantee = models.CharField(max_length=200)  # Can be hospital, lab, insurance
    grantee_type = models.CharField(max_length=20, choices=[
        ('HOSPITAL', 'Hospital'),
        ('LAB', 'Laboratory'),
        ('INSURANCE', 'Insurance'),
        ('DOCTOR', 'Doctor'),
    ])
    permission_type = models.CharField(max_length=10, choices=PERMISSION_TYPES)
    purpose = models.TextField()  # Purpose for access (HIPAA requirement)

    # Cryptographic authorization
    signature = models.TextField()
    zk_proof = models.TextField(blank=True)

    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'access_permissions'

    def __str__(self):
        return f"Permission-{self.grantee_type}-{self.record.record_id[:16]}"


class AuditLog(models.Model):
    """Audit trail for all data access"""
    ACTION_TYPES = [
        ('CREATE', 'Record Created'),
        ('READ', 'Record Accessed'),
        ('UPDATE', 'Record Updated'),
        ('SHARE', 'Record Shared'),
        ('DELETE', 'Record Deleted'),
        ('ACCESS_DENIED', 'Access Denied'),
    ]

    log_id = models.CharField(max_length=255, unique=True)
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE)
    actor = models.CharField(max_length=200)
    actor_type = models.CharField(max_length=20)
    action = models.CharField(max_length=15, choices=ACTION_TYPES)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit-{self.action}-{self.timestamp}"
