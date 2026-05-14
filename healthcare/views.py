"""
MediChain Healthcare Views
Template rendering + API endpoints for patient records, access control
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import (
    Patient, Hospital, Laboratory, InsuranceProvider,
    MedicalRecord, AccessPermission, AuditLog
)
from blockchain.models import Transaction, BlockchainNetwork
from zk_proofs.zk_service import ZKProofService
from api.serializers import PatientSerializer, HospitalSerializer, MedicalRecordSerializer


# ==================== TEMPLATE VIEWS ====================

def healthcare_dashboard(request):
    """Healthcare dashboard"""
    context = {
        'patient_count': Patient.objects.filter(is_active=True).count(),
        'hospital_count': Hospital.objects.count(),
        'record_count': MedicalRecord.objects.filter(is_active=True).count(),
        'permission_count': AccessPermission.objects.filter(is_active=True).count(),
        'recent_patients': Patient.objects.order_by('-created_at')[:5],
        'recent_records': MedicalRecord.objects.order_by('-created_at')[:5],
        'hospitals': Hospital.objects.all(),
    }
    return render(request, 'healthcare/dashboard.html', context)


def patient_list(request):
    """List all patients"""
    patients = Patient.objects.order_by('-created_at')
    return render(request, 'healthcare/patient_list.html', {'patients': patients})


def patient_add(request):
    """Add patient form"""
    if request.method == 'POST':
        patient = Patient.objects.create(
            public_key=request.POST.get('public_key'),
            date_of_birth=request.POST.get('date_of_birth') or None,
            blood_type=request.POST.get('blood_type', ''),
            allergies=request.POST.get('allergies', ''),
            emergency_contact=request.POST.get('emergency_contact', ''),
        )
        messages.success(request, f'Patient registered: {patient.patient_id[:16]}...')
        return redirect('patient_list')
    return render(request, 'healthcare/patient_add.html')


def patient_detail(request, patient_id):
    """Patient detail page"""
    patient = get_object_or_404(Patient, patient_id=patient_id)
    records = MedicalRecord.objects.filter(patient=patient, is_active=True)
    permissions = AccessPermission.objects.filter(grantor=patient)
    return render(request, 'healthcare/patient_detail.html', {
        'patient': patient, 'records': records, 'permissions': permissions
    })


def hospital_list(request):
    """List all hospitals"""
    hospitals = Hospital.objects.order_by('-created_at')
    return render(request, 'healthcare/hospital_list.html', {'hospitals': hospitals})


def hospital_add(request):
    """Add hospital form"""
    if request.method == 'POST':
        network_id = request.POST.get('blockchain_network')
        network = None
        if network_id:
            network = BlockchainNetwork.objects.filter(id=network_id).first()

        hospital = Hospital.objects.create(
            name=request.POST.get('name'),
            address=request.POST.get('address', ''),
            license_number=request.POST.get('license_number'),
            public_key=request.POST.get('public_key'),
            blockchain_network=network,
        )
        messages.success(request, f'Hospital registered: {hospital.name}')
        return redirect('hospital_list')

    networks = BlockchainNetwork.objects.filter(is_active=True)
    return render(request, 'healthcare/hospital_add.html', {'networks': networks})


def hospital_detail(request, hospital_id):
    """Hospital detail page"""
    hospital = get_object_or_404(Hospital, hospital_id=hospital_id)
    records = MedicalRecord.objects.filter(hospital=hospital)
    return render(request, 'healthcare/hospital_detail.html', {
        'hospital': hospital, 'records': records
    })


def record_list(request):
    """List all medical records"""
    records = MedicalRecord.objects.order_by('-created_at')
    return render(request, 'healthcare/record_list.html', {'records': records})


def record_add(request):
    """Create medical record form"""
    if request.method == 'POST':
        patient = get_object_or_404(Patient, patient_id=request.POST.get('patient_id'))
        hospital = get_object_or_404(Hospital, hospital_id=request.POST.get('hospital_id'))

        record = MedicalRecord.objects.create(
            patient=patient,
            hospital=hospital,
            record_type=request.POST.get('record_type', 'DIAGNOSIS'),
            title=request.POST.get('title'),
            description=request.POST.get('description', ''),
            ipfs_hash=request.POST.get('ipfs_hash', ''),
        )

        # Create blockchain transaction
        tx = Transaction.objects.create(
            tx_type='CREATE',
            sender=hospital.hospital_id,
            data_hash=record.data_hash,
            signature=request.POST.get('signature', ''),
            status='PENDING'
        )
        record.blockchain_tx = tx
        record.save()

        # Audit log
        AuditLog.objects.create(
            log_id=f"audit_{record.record_id}_create",
            record=record,
            actor=hospital.hospital_id,
            actor_type='HOSPITAL',
            action='CREATE',
            details={'record_type': record.record_type, 'title': record.title}
        )

        messages.success(request, f'Record created: {record.record_id[:16]}...')
        return redirect('record_list')

    context = {
        'patients': Patient.objects.filter(is_active=True),
        'hospitals': Hospital.objects.all(),
        'selected_patient': request.GET.get('patient', ''),
        'selected_hospital': request.GET.get('hospital', ''),
    }
    return render(request, 'healthcare/record_add.html', context)


def record_detail(request, record_id):
    """Medical record detail"""
    record = get_object_or_404(MedicalRecord, record_id=record_id)
    permissions = AccessPermission.objects.filter(record=record)
    audit_logs = AuditLog.objects.filter(record=record).order_by('-timestamp')
    return render(request, 'healthcare/record_detail.html', {
        'record': record, 'permissions': permissions, 'audit_logs': audit_logs
    })


def permission_add(request):
    """Grant access permission form"""
    if request.method == 'POST':
        record = get_object_or_404(MedicalRecord, record_id=request.POST.get('record_id'))
        patient = get_object_or_404(Patient, patient_id=request.POST.get('patient_id'))

        permission = AccessPermission.objects.create(
            record=record,
            grantor=patient,
            grantee=request.POST.get('grantee'),
            grantee_type=request.POST.get('grantee_type', 'HOSPITAL'),
            permission_type=request.POST.get('permission_type', 'READ'),
            purpose=request.POST.get('purpose', 'Medical treatment'),
            signature=request.POST.get('signature', ''),
            valid_until=request.POST.get('valid_until') or None,
        )

        AuditLog.objects.create(
            log_id=f"audit_{record.record_id}_grant",
            record=record,
            actor=patient.patient_id,
            actor_type='PATIENT',
            action='SHARE',
            details={
                'grantee': permission.grantee,
                'permission_type': permission.permission_type,
                'purpose': permission.purpose,
            }
        )

        messages.success(request, 'Access permission granted successfully')
        return redirect('healthcare_dashboard')

    context = {
        'records': MedicalRecord.objects.filter(is_active=True),
        'patients': Patient.objects.filter(is_active=True),
        'selected_record': request.GET.get('record', ''),
        'selected_patient': request.GET.get('patient', ''),
    }
    return render(request, 'healthcare/permission_add.html', context)


# ==================== API VIEWSETS ====================

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        data = request.data
        patient = Patient.objects.create(
            public_key=data.get('public_key'),
            date_of_birth=data.get('date_of_birth'),
            blood_type=data.get('blood_type', ''),
            allergies=data.get('allergies', ''),
            emergency_contact=data.get('emergency_contact', ''),
        )
        return Response({
            'patient_id': patient.patient_id,
            'public_key': patient.public_key,
            'status': 'registered'
        }, status=201)

    def retrieve(self, request, pk=None):
        patient = get_object_or_404(Patient, patient_id=pk)
        return Response({
            'patient_id': patient.patient_id,
            'public_key': patient.public_key,
            'blood_type': patient.blood_type,
            'allergies': patient.allergies,
            'created_at': patient.created_at,
        })

    @action(detail=True, methods=['get'])
    def records(self, request, pk=None):
        patient = get_object_or_404(Patient, patient_id=pk)
        records = MedicalRecord.objects.filter(patient=patient, is_active=True)
        data = [{
            'record_id': r.record_id, 'record_type': r.record_type,
            'title': r.title, 'hospital': r.hospital.name,
            'data_hash': r.data_hash, 'created_at': r.created_at,
        } for r in records]
        return Response(data)


class HospitalViewSet(viewsets.ModelViewSet):
    queryset = Hospital.objects.order_by('-created_at')
    serializer_class = HospitalSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        data = request.data
        hospital = Hospital.objects.create(
            name=data.get('name'),
            address=data.get('address'),
            license_number=data.get('license_number'),
            public_key=data.get('public_key'),
        )
        return Response({
            'hospital_id': hospital.hospital_id,
            'name': hospital.name,
            'status': 'registered'
        }, status=201)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request):
        data = request.data
        patient = get_object_or_404(Patient, patient_id=data.get('patient_id'))
        hospital = get_object_or_404(Hospital, hospital_id=data.get('hospital_id'))

        record = MedicalRecord.objects.create(
            patient=patient, hospital=hospital,
            record_type=data.get('record_type', 'DIAGNOSIS'),
            title=data.get('title'),
            description=data.get('description'),
            ipfs_hash=data.get('ipfs_hash', ''),
            file_size=data.get('file_size', 0),
        )

        tx = Transaction.objects.create(
            tx_type='CREATE', sender=hospital.hospital_id,
            data_hash=record.data_hash,
            signature=data.get('signature', ''), status='PENDING'
        )
        record.blockchain_tx = tx
        record.save()

        AuditLog.objects.create(
            log_id=f"audit_{record.record_id}_create",
            record=record, actor=hospital.hospital_id,
            actor_type='HOSPITAL', action='CREATE',
            details={'record_type': record.record_type, 'title': record.title}
        )

        return Response({
            'record_id': record.record_id,
            'data_hash': record.data_hash,
            'tx_hash': tx.tx_hash,
            'status': 'created'
        }, status=201)

    def retrieve(self, request, pk=None):
        record = get_object_or_404(MedicalRecord, record_id=pk)
        return Response({
            'record_id': record.record_id,
            'record_type': record.record_type,
            'title': record.title,
            'description': record.description,
            'patient_id': record.patient.patient_id,
            'hospital': record.hospital.name,
            'data_hash': record.data_hash,
            'ipfs_hash': record.ipfs_hash,
            'created_at': record.created_at,
        })

    @action(detail=True, methods=['post'])
    def grant_access(self, request, pk=None):
        record = get_object_or_404(MedicalRecord, record_id=pk)
        data = request.data
        patient = record.patient

        permission = AccessPermission.objects.create(
            record=record, grantor=patient,
            grantee=data.get('grantee'),
            grantee_type=data.get('grantee_type', 'HOSPITAL'),
            permission_type=data.get('permission_type', 'READ'),
            purpose=data.get('purpose', 'Medical treatment'),
            signature=data.get('signature'),
            valid_until=data.get('valid_until'),
        )
        return Response({
            'permission_id': permission.permission_id,
            'grantee': permission.grantee,
            'permission_type': permission.permission_type,
        })

    @action(detail=True, methods=['post'])
    def verify_integrity(self, request, pk=None):
        record = get_object_or_404(MedicalRecord, record_id=pk)
        computed_hash = record.calculate_hash()
        return Response({
            'record_id': record.record_id,
            'stored_hash': record.data_hash,
            'computed_hash': computed_hash,
            'is_valid': computed_hash == record.data_hash,
        })

    @action(detail=True, methods=['post'])
    def zk_verify(self, request, pk=None):
        record = get_object_or_404(MedicalRecord, record_id=pk)
        zk_service = ZKProofService()
        proof = request.data.get('proof')
        is_valid = zk_service.verify_proof(proof, record.data_hash, [record.record_id])
        return Response({
            'record_id': record.record_id,
            'is_valid': is_valid,
            'verification_type': 'zero_knowledge',
            'data_revealed': False,
        })


class AuditLogViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        record_id = request.query_params.get('record_id')
        actor = request.query_params.get('actor')
        logs = AuditLog.objects.all()
        if record_id:
            logs = logs.filter(record__record_id=record_id)
        if actor:
            logs = logs.filter(actor=actor)
        logs = logs[:100]
        data = [{
            'log_id': l.log_id, 'record_id': l.record.record_id,
            'actor': l.actor, 'action': l.action,
            'details': l.details, 'timestamp': l.timestamp,
        } for l in logs]
        return Response(data)
