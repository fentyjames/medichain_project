"""
MediChain Healthcare Views
Template rendering + API endpoints for patient records, access control
"""

import hashlib
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import HospitalSerializer, MedicalRecordSerializer, PatientSerializer
from blockchain.models import BlockchainNetwork, Transaction
from zk_proofs.zk_service import ZKProofService

from .models import AccessPermission, AuditLog, Hospital, InsuranceProvider, Laboratory, MedicalRecord, Patient


def _paginate(request, qs, per_page=25):
    """Return (page_obj, query_string) for a queryset."""
    paginator = Paginator(qs, per_page)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    params = request.GET.copy()
    params.pop('page', None)
    qs_str = ('?' + params.urlencode() + '&') if params.urlencode() else '?'
    return page_obj, qs_str


# ==================== TEMPLATE VIEWS ====================

@login_required(login_url='/accounts/login/')
def healthcare_dashboard(request):
    """Healthcare dashboard"""
    context = {
        'patient_count': Patient.objects.filter(is_active=True).count(),
        'hospital_count': Hospital.objects.count(),
        'record_count': MedicalRecord.objects.filter(is_active=True).count(),
        'permission_count': AccessPermission.objects.filter(is_active=True).count(),
        'recent_patients': Patient.objects.select_related('user').order_by('-created_at')[:5],
        'recent_records': MedicalRecord.objects.select_related('hospital', 'patient').order_by('-created_at')[:5],
        'hospitals': Hospital.objects.all()[:6],
    }
    return render(request, 'healthcare/dashboard.html', context)


@login_required(login_url='/accounts/login/')
def patient_list(request):
    """List all patients with search."""
    q = request.GET.get('q', '').strip()
    qs = Patient.objects.select_related('user').order_by('-created_at')
    if q:
        qs = qs.filter(
            Q(patient_id__icontains=q) |
            Q(blood_type__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(user__username__icontains=q)
        )
    page_obj, qs_str = _paginate(request, qs, 25)
    return render(request, 'healthcare/patient_list.html', {
        'patients': page_obj,
        'page_obj': page_obj,
        'query_string': qs_str,
        'q': q,
    })


@login_required(login_url='/accounts/login/')
def patient_add(request):
    """Add patient form."""
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


@login_required(login_url='/accounts/login/')
def patient_detail(request, patient_id):
    """Patient detail page."""
    patient = get_object_or_404(Patient.objects.select_related('user'), patient_id=patient_id)
    records = MedicalRecord.objects.filter(patient=patient, is_active=True).select_related('hospital', 'blockchain_tx')
    permissions = AccessPermission.objects.filter(grantor=patient)
    return render(request, 'healthcare/patient_detail.html', {
        'patient': patient, 'records': records, 'permissions': permissions,
    })


@login_required(login_url='/accounts/login/')
def hospital_list(request):
    """List all hospitals with search."""
    q = request.GET.get('q', '').strip()
    qs = Hospital.objects.order_by('name')
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(license_number__icontains=q) |
            Q(address__icontains=q)
        )
    page_obj, qs_str = _paginate(request, qs, 12)
    return render(request, 'healthcare/hospital_list.html', {
        'hospitals': page_obj,
        'page_obj': page_obj,
        'query_string': qs_str,
        'q': q,
    })


@login_required(login_url='/accounts/login/')
def hospital_add(request):
    """Add hospital form."""
    if request.method == 'POST':
        network_id = request.POST.get('blockchain_network')
        network = BlockchainNetwork.objects.filter(id=network_id).first() if network_id else None
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


@login_required(login_url='/accounts/login/')
def hospital_detail(request, hospital_id):
    """Hospital detail page."""
    hospital = get_object_or_404(Hospital, hospital_id=hospital_id)
    records = MedicalRecord.objects.filter(hospital=hospital).select_related('patient__user')
    return render(request, 'healthcare/hospital_detail.html', {
        'hospital': hospital, 'records': records,
    })


@login_required(login_url='/accounts/login/')
def record_list(request):
    """List all medical records with search + type filter."""
    q = request.GET.get('q', '').strip()
    record_type = request.GET.get('type', '').strip()
    qs = MedicalRecord.objects.select_related('patient__user', 'hospital', 'blockchain_tx').order_by('-created_at')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(record_id__icontains=q))
    if record_type:
        qs = qs.filter(record_type=record_type)
    page_obj, qs_str = _paginate(request, qs, 25)
    return render(request, 'healthcare/record_list.html', {
        'records': page_obj,
        'page_obj': page_obj,
        'query_string': qs_str,
        'q': q,
        'selected_type': record_type,
    })


@login_required(login_url='/accounts/login/')
def record_add(request):
    """Create medical record form."""
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
            metadata_hash=request.POST.get('metadata_hash', ''),
        )
        tx = Transaction.objects.create(
            tx_type='CREATE',
            sender=hospital.hospital_id,
            data_hash=record.data_hash,
            signature=request.POST.get('signature', ''),
            status='PENDING',
        )
        record.blockchain_tx = tx
        record.save()
        AuditLog.objects.create(
            log_id=f"audit_{record.record_id}_create",
            record=record,
            actor=hospital.hospital_id,
            actor_type='HOSPITAL',
            action='CREATE',
            details={'record_type': record.record_type, 'title': record.title},
        )
        messages.success(request, f'Record created: {record.record_id[:16]}...')
        return redirect('record_list')
    context = {
        'patients': Patient.objects.filter(is_active=True).select_related('user'),
        'hospitals': Hospital.objects.all(),
        'selected_patient': request.GET.get('patient', ''),
        'selected_hospital': request.GET.get('hospital', ''),
    }
    return render(request, 'healthcare/record_add.html', context)


@login_required(login_url='/accounts/login/')
def record_detail(request, record_id):
    """Medical record detail."""
    record = get_object_or_404(
        MedicalRecord.objects.select_related('patient__user', 'hospital', 'blockchain_tx'),
        record_id=record_id,
    )
    permissions = AccessPermission.objects.filter(record=record)
    audit_logs = AuditLog.objects.filter(record=record).order_by('-timestamp')
    return render(request, 'healthcare/record_detail.html', {
        'record': record, 'permissions': permissions, 'audit_logs': audit_logs,
    })


@login_required(login_url='/accounts/login/')
def permission_add(request):
    """Grant access permission form."""
    if request.method == 'POST':
        record = get_object_or_404(MedicalRecord, record_id=request.POST.get('record_id'))
        patient = get_object_or_404(Patient, patient_id=request.POST.get('patient_id'))
        permission = AccessPermission.objects.create(
            permission_id=f"perm_{record.record_id[:16]}_{timezone.now().timestamp()}",
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
            log_id=f"audit_{record.record_id}_grant_{permission.permission_id[:8]}",
            record=record,
            actor=patient.patient_id,
            actor_type='PATIENT',
            action='SHARE',
            details={
                'grantee': permission.grantee,
                'permission_type': permission.permission_type,
                'purpose': permission.purpose,
            },
        )
        messages.success(request, 'Access permission granted successfully')
        return redirect('healthcare_dashboard')
    context = {
        'records': MedicalRecord.objects.filter(is_active=True).select_related('patient__user'),
        'patients': Patient.objects.filter(is_active=True).select_related('user'),
        'selected_record': request.GET.get('record', ''),
        'selected_patient': request.GET.get('patient', ''),
    }
    return render(request, 'healthcare/permission_add.html', context)


# ==================== PATIENT EDIT / DELETE ====================

@login_required(login_url='/accounts/login/')
def patient_edit(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    if request.method == 'POST':
        patient.date_of_birth = request.POST.get('date_of_birth') or None
        patient.blood_type = request.POST.get('blood_type', '')
        patient.allergies = request.POST.get('allergies', '')
        patient.emergency_contact = request.POST.get('emergency_contact', '')
        patient.is_active = 'is_active' in request.POST
        patient.save()
        messages.success(request, 'Patient updated successfully.')
        return redirect('patient_detail', patient_id=patient_id)
    return render(request, 'healthcare/patient_edit.html', {'patient': patient})


@login_required(login_url='/accounts/login/')
def patient_delete(request, patient_id):
    patient = get_object_or_404(Patient, patient_id=patient_id)
    if request.method == 'POST':
        name = patient.user.get_full_name() if patient.user else patient.patient_id[:16]
        patient.delete()
        messages.success(request, f'Patient "{name}" deleted.')
        return redirect('patient_list')
    return render(request, 'healthcare/patient_edit.html', {'patient': patient, 'confirm_delete': True})


# ==================== HOSPITAL EDIT / DELETE ====================

@login_required(login_url='/accounts/login/')
def hospital_edit(request, hospital_id):
    hospital = get_object_or_404(Hospital, hospital_id=hospital_id)
    if request.method == 'POST':
        hospital.name = request.POST.get('name', hospital.name)
        hospital.address = request.POST.get('address', hospital.address)
        hospital.license_number = request.POST.get('license_number', hospital.license_number)
        hospital.is_verified = 'is_verified' in request.POST
        network_id = request.POST.get('blockchain_network')
        if network_id:
            hospital.blockchain_network = BlockchainNetwork.objects.filter(id=network_id).first()
        hospital.save()
        messages.success(request, f'Hospital "{hospital.name}" updated.')
        return redirect('hospital_detail', hospital_id=hospital_id)
    networks = BlockchainNetwork.objects.filter(is_active=True)
    return render(request, 'healthcare/hospital_edit.html', {'hospital': hospital, 'networks': networks})


@login_required(login_url='/accounts/login/')
def hospital_delete(request, hospital_id):
    hospital = get_object_or_404(Hospital, hospital_id=hospital_id)
    if request.method == 'POST':
        name = hospital.name
        hospital.delete()
        messages.success(request, f'Hospital "{name}" deleted.')
        return redirect('hospital_list')
    networks = BlockchainNetwork.objects.filter(is_active=True)
    return render(request, 'healthcare/hospital_edit.html', {
        'hospital': hospital, 'networks': networks, 'confirm_delete': True,
    })


# ==================== RECORD EDIT / ARCHIVE ====================

@login_required(login_url='/accounts/login/')
def record_edit(request, record_id):
    record = get_object_or_404(MedicalRecord, record_id=record_id)
    if request.method == 'POST':
        record.title = request.POST.get('title', record.title)
        record.description = request.POST.get('description', record.description)
        record.record_type = request.POST.get('record_type', record.record_type)
        record.ipfs_hash = request.POST.get('ipfs_hash', record.ipfs_hash)
        record.save()
        AuditLog.objects.create(
            log_id=f"audit_{record.record_id}_edit_{int(timezone.now().timestamp())}",
            record=record,
            actor=request.user.username,
            actor_type='DOCTOR',
            action='UPDATE',
            details={'title': record.title, 'record_type': record.record_type},
        )
        messages.success(request, 'Record updated.')
        return redirect('record_detail', record_id=record_id)
    return render(request, 'healthcare/record_edit.html', {'record': record})


@login_required(login_url='/accounts/login/')
def record_archive(request, record_id):
    record = get_object_or_404(MedicalRecord, record_id=record_id)
    if request.method == 'POST':
        record.is_active = False
        record.save()
        AuditLog.objects.create(
            log_id=f"audit_{record.record_id}_archive_{int(timezone.now().timestamp())}",
            record=record,
            actor=request.user.username,
            actor_type='DOCTOR',
            action='DELETE',
            details={'archived': True},
        )
        messages.success(request, 'Record archived.')
        return redirect('record_list')
    return render(request, 'healthcare/record_edit.html', {'record': record, 'confirm_archive': True})


# ==================== LABORATORY ====================

@login_required(login_url='/accounts/login/')
def laboratory_list(request):
    q = request.GET.get('q', '').strip()
    qs = Laboratory.objects.select_related('hospital').order_by('name')
    if q:
        qs = qs.filter(
            Q(name__icontains=q) | Q(accreditation__icontains=q) | Q(hospital__name__icontains=q)
        )
    page_obj, qs_str = _paginate(request, qs, 12)
    return render(request, 'healthcare/laboratory_list.html', {
        'labs': page_obj, 'page_obj': page_obj, 'query_string': qs_str, 'q': q,
    })


@login_required(login_url='/accounts/login/')
def laboratory_detail(request, lab_id):
    lab = get_object_or_404(Laboratory.objects.select_related('hospital'), lab_id=lab_id)
    return render(request, 'healthcare/laboratory_detail.html', {'lab': lab})


@login_required(login_url='/accounts/login/')
def laboratory_add(request):
    if request.method == 'POST':
        lab = Laboratory.objects.create(
            lab_id=hashlib.sha256(f"lab_{uuid.uuid4()}".encode()).hexdigest(),
            name=request.POST.get('name'),
            accreditation=request.POST.get('accreditation', ''),
            public_key=request.POST.get('public_key', ''),
            hospital=Hospital.objects.filter(
                hospital_id=request.POST.get('hospital_id')
            ).first(),
        )
        messages.success(request, f'Laboratory "{lab.name}" registered.')
        return redirect('laboratory_list')
    hospitals = Hospital.objects.order_by('name')
    return render(request, 'healthcare/laboratory_add.html', {'hospitals': hospitals})


# ==================== INSURANCE PROVIDER ====================

@login_required(login_url='/accounts/login/')
def insurance_list(request):
    q = request.GET.get('q', '').strip()
    qs = InsuranceProvider.objects.order_by('name')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(license_number__icontains=q))
    page_obj, qs_str = _paginate(request, qs, 12)
    return render(request, 'healthcare/insurance_list.html', {
        'providers': page_obj, 'page_obj': page_obj, 'query_string': qs_str, 'q': q,
    })


@login_required(login_url='/accounts/login/')
def insurance_detail(request, provider_id):
    provider = get_object_or_404(InsuranceProvider, provider_id=provider_id)
    return render(request, 'healthcare/insurance_detail.html', {'provider': provider})


@login_required(login_url='/accounts/login/')
def insurance_add(request):
    if request.method == 'POST':
        provider = InsuranceProvider.objects.create(
            provider_id=hashlib.sha256(f"ins_{uuid.uuid4()}".encode()).hexdigest(),
            name=request.POST.get('name'),
            license_number=request.POST.get('license_number', ''),
            public_key=request.POST.get('public_key', ''),
        )
        messages.success(request, f'Insurance provider "{provider.name}" registered.')
        return redirect('insurance_list')
    return render(request, 'healthcare/insurance_add.html')


# ==================== ACCESS PERMISSIONS LIST / REVOKE ====================

@login_required(login_url='/accounts/login/')
def permission_list(request):
    grantee_type = request.GET.get('grantee_type', '').strip()
    active_only = request.GET.get('active', '').strip()
    qs = AccessPermission.objects.select_related('record', 'grantor__user').order_by('-created_at')
    if grantee_type:
        qs = qs.filter(grantee_type=grantee_type)
    if active_only == '1':
        qs = qs.filter(is_active=True)
    page_obj, qs_str = _paginate(request, qs, 25)
    return render(request, 'healthcare/permission_list.html', {
        'permissions': page_obj, 'page_obj': page_obj, 'query_string': qs_str,
        'selected_grantee_type': grantee_type, 'active_only': active_only,
    })


@login_required(login_url='/accounts/login/')
def permission_revoke(request, permission_id):
    perm = get_object_or_404(AccessPermission, permission_id=permission_id)
    if request.method == 'POST':
        perm.is_active = False
        perm.save()
        AuditLog.objects.create(
            log_id=f"audit_{perm.record.record_id}_revoke_{int(timezone.now().timestamp())}",
            record=perm.record,
            actor=request.user.username,
            actor_type='DOCTOR',
            action='UPDATE',
            details={'permission_id': permission_id, 'revoked': True},
        )
        messages.success(request, 'Permission revoked.')
        return redirect('permission_list')
    return redirect('permission_list')


# ==================== AUDIT LOG ====================

@login_required(login_url='/accounts/login/')
def audit_log_list(request):
    action_filter = request.GET.get('action', '').strip()
    actor_type_filter = request.GET.get('actor_type', '').strip()
    qs = AuditLog.objects.select_related('record').order_by('-timestamp')
    if action_filter:
        qs = qs.filter(action=action_filter)
    if actor_type_filter:
        qs = qs.filter(actor_type=actor_type_filter)
    page_obj, qs_str = _paginate(request, qs, 25)
    return render(request, 'healthcare/audit_log_list.html', {
        'logs': page_obj, 'page_obj': page_obj, 'query_string': qs_str,
        'selected_action': action_filter, 'selected_actor_type': actor_type_filter,
    })


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
        return Response({'patient_id': patient.patient_id, 'public_key': patient.public_key, 'status': 'registered'}, status=201)

    def retrieve(self, request, pk=None):
        patient = get_object_or_404(Patient, patient_id=pk)
        return Response({
            'patient_id': patient.patient_id, 'public_key': patient.public_key,
            'blood_type': patient.blood_type, 'allergies': patient.allergies,
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
            name=data.get('name'), address=data.get('address'),
            license_number=data.get('license_number'), public_key=data.get('public_key'),
        )
        return Response({'hospital_id': hospital.hospital_id, 'name': hospital.name, 'status': 'registered'}, status=201)


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
            title=data.get('title'), description=data.get('description'),
            ipfs_hash=data.get('ipfs_hash', ''), file_size=data.get('file_size', 0),
        )
        tx = Transaction.objects.create(
            tx_type='CREATE', sender=hospital.hospital_id,
            data_hash=record.data_hash, signature=data.get('signature', ''), status='PENDING',
        )
        record.blockchain_tx = tx
        record.save()
        AuditLog.objects.create(
            log_id=f"audit_{record.record_id}_create", record=record,
            actor=hospital.hospital_id, actor_type='HOSPITAL', action='CREATE',
            details={'record_type': record.record_type, 'title': record.title},
        )
        return Response({'record_id': record.record_id, 'data_hash': record.data_hash, 'tx_hash': tx.tx_hash, 'status': 'created'}, status=201)

    def retrieve(self, request, pk=None):
        record = get_object_or_404(MedicalRecord, record_id=pk)
        return Response({
            'record_id': record.record_id, 'record_type': record.record_type,
            'title': record.title, 'description': record.description,
            'patient_id': record.patient.patient_id, 'hospital': record.hospital.name,
            'data_hash': record.data_hash, 'ipfs_hash': record.ipfs_hash, 'created_at': record.created_at,
        })

    @action(detail=True, methods=['post'])
    def grant_access(self, request, pk=None):
        record = get_object_or_404(MedicalRecord, record_id=pk)
        data = request.data
        permission = AccessPermission.objects.create(
            record=record, grantor=record.patient,
            grantee=data.get('grantee'), grantee_type=data.get('grantee_type', 'HOSPITAL'),
            permission_type=data.get('permission_type', 'READ'),
            purpose=data.get('purpose', 'Medical treatment'), signature=data.get('signature', ''),
            valid_until=data.get('valid_until'),
        )
        return Response({'permission_id': permission.permission_id, 'grantee': permission.grantee, 'permission_type': permission.permission_type})

    @action(detail=True, methods=['post'])
    def verify_integrity(self, request, pk=None):
        record = get_object_or_404(MedicalRecord, record_id=pk)
        computed_hash = record.calculate_hash()
        return Response({'record_id': record.record_id, 'stored_hash': record.data_hash, 'computed_hash': computed_hash, 'is_valid': computed_hash == record.data_hash})

    @action(detail=True, methods=['post'])
    def zk_verify(self, request, pk=None):
        record = get_object_or_404(MedicalRecord, record_id=pk)
        zk_service = ZKProofService()
        proof = request.data.get('proof')
        is_valid = zk_service.verify_proof(proof, record.data_hash, [record.record_id])
        return Response({'record_id': record.record_id, 'is_valid': is_valid, 'verification_type': 'zero_knowledge', 'data_revealed': False})


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
            'log_id': log.log_id, 'record_id': log.record.record_id,
            'actor': log.actor, 'action': log.action,
            'details': log.details, 'timestamp': log.timestamp,
        } for log in logs]
        return Response(data)
