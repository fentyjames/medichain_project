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
from blockchain.models import Block, BlockchainNetwork, RollupBatch, Transaction
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
        record_id = request.POST.get('record_id')
        if record_id:
            return redirect('record_detail', record_id=record_id)
        return redirect('healthcare_dashboard')
    context = {
        'records': MedicalRecord.objects.filter(is_active=True).select_related('patient__user'),
        'patients': Patient.objects.filter(is_active=True).select_related('user'),
        'selected_record': request.GET.get('record', ''),
        'selected_patient': request.GET.get('patient', ''),
    }
    return render(request, 'healthcare/permission_add.html', context)


# ==================== PATIENT REPORT ====================

@login_required(login_url='/accounts/login/')
def patient_report(request, patient_id):
    """Printable patient report — full medical summary for a single patient."""
    patient = get_object_or_404(Patient.objects.select_related('user'), patient_id=patient_id)
    records = MedicalRecord.objects.filter(patient=patient).select_related(
        'hospital', 'blockchain_tx'
    ).order_by('-created_at')
    permissions = AccessPermission.objects.filter(grantor=patient).select_related('record').order_by('-created_at')
    audit_logs = AuditLog.objects.filter(record__patient=patient).order_by('-timestamp')[:50]

    total_records = records.count()
    active_permissions = permissions.filter(is_active=True).count()

    # Build record-type breakdown with percentages for the bar chart
    type_counts = {}
    for r in records:
        label = r.get_record_type_display()
        type_counts[label] = type_counts.get(label, 0) + 1
    record_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / total_records * 100) if total_records else 0}
        for label, count in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    return render(request, 'healthcare/patient_report.html', {
        'patient': patient,
        'records': records,
        'permissions': permissions,
        'audit_logs': audit_logs,
        'record_breakdown': record_breakdown,
        'total_records': total_records,
        'active_permissions': active_permissions,
        'generated_at': timezone.now(),
    })


# ==================== PATIENT PRINT REPORT ====================

@login_required(login_url='/accounts/login/')
def patient_print_report(request, patient_id):
    """Standalone printable medical report for a single patient — no site chrome."""
    patient = get_object_or_404(Patient.objects.select_related('user'), patient_id=patient_id)
    records = MedicalRecord.objects.filter(patient=patient).select_related(
        'hospital', 'blockchain_tx'
    ).order_by('-created_at')
    permissions = AccessPermission.objects.filter(grantor=patient).select_related('record').order_by('-created_at')
    audit_logs = AuditLog.objects.filter(record__patient=patient).order_by('-timestamp')[:30]

    total_records = records.count()
    active_permissions = permissions.filter(is_active=True).count()

    type_counts = {}
    for r in records:
        label = r.get_record_type_display()
        type_counts[label] = type_counts.get(label, 0) + 1
    record_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / total_records * 100) if total_records else 0}
        for label, count in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    return render(request, 'healthcare/patient_print_report.html', {
        'patient': patient,
        'records': records,
        'permissions': permissions,
        'audit_logs': audit_logs,
        'record_breakdown': record_breakdown,
        'total_records': total_records,
        'active_permissions': active_permissions,
        'generated_at': timezone.now(),
        'generated_by': request.user.get_full_name() or request.user.username,
    })


# ==================== HOSPITAL PRINT REPORT ====================

@login_required(login_url='/accounts/login/')
def hospital_print_report(request, hospital_id):
    """Standalone printable report for a single hospital."""
    hospital = get_object_or_404(Hospital, hospital_id=hospital_id)
    records = MedicalRecord.objects.filter(hospital=hospital).select_related(
        'patient__user', 'blockchain_tx'
    ).order_by('-created_at')
    labs = Laboratory.objects.filter(hospital=hospital).order_by('name')
    audit_logs = AuditLog.objects.filter(record__hospital=hospital).order_by('-timestamp')[:30]

    total_records = records.count()
    unique_patients = records.values('patient').distinct().count()

    type_counts = {}
    for r in records:
        label = r.get_record_type_display()
        type_counts[label] = type_counts.get(label, 0) + 1
    record_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / total_records * 100) if total_records else 0}
        for label, count in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    return render(request, 'healthcare/hospital_print_report.html', {
        'hospital': hospital,
        'records': records,
        'labs': labs,
        'audit_logs': audit_logs,
        'record_breakdown': record_breakdown,
        'total_records': total_records,
        'unique_patients': unique_patients,
        'generated_at': timezone.now(),
        'generated_by': request.user.get_full_name() or request.user.username,
    })


# ==================== LABORATORY PRINT REPORT ====================

@login_required(login_url='/accounts/login/')
def laboratory_print_report(request, lab_id):
    """Standalone printable report for a single laboratory."""
    lab = get_object_or_404(Laboratory.objects.select_related('hospital'), lab_id=lab_id)

    lab_records = MedicalRecord.objects.none()
    hospital_records = MedicalRecord.objects.none()
    if lab.hospital:
        hospital_records = MedicalRecord.objects.filter(hospital=lab.hospital).select_related('patient__user').order_by('-created_at')
        lab_records = hospital_records.filter(record_type='LAB_RESULT')

    permissions = AccessPermission.objects.filter(
        grantee_type='LAB', grantee__icontains=lab.name
    ).select_related('record', 'grantor__user').order_by('-created_at')

    return render(request, 'healthcare/laboratory_print_report.html', {
        'lab': lab,
        'lab_records': lab_records[:100],
        'permissions': permissions,
        'total_lab_results': lab_records.count(),
        'total_hospital_records': hospital_records.count(),
        'generated_at': timezone.now(),
        'generated_by': request.user.get_full_name() or request.user.username,
    })


# ==================== INSURANCE PRINT REPORT ====================

@login_required(login_url='/accounts/login/')
def insurance_print_report(request, provider_id):
    """Standalone printable report for a single insurance provider."""
    provider = get_object_or_404(InsuranceProvider, provider_id=provider_id)

    permissions = AccessPermission.objects.filter(
        grantee_type='INSURANCE', grantee__icontains=provider.name
    ).select_related('record__patient__user', 'grantor__user').order_by('-created_at')

    claims = MedicalRecord.objects.filter(
        record_type='INSURANCE', is_active=True
    ).select_related('patient__user', 'hospital').order_by('-created_at')

    return render(request, 'healthcare/insurance_print_report.html', {
        'provider': provider,
        'permissions': permissions,
        'claims': claims,
        'total_permissions': permissions.count(),
        'active_permissions': permissions.filter(is_active=True).count(),
        'generated_at': timezone.now(),
        'generated_by': request.user.get_full_name() or request.user.username,
    })


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


# ==================== LABORATORY EDIT / DELETE ====================

@login_required(login_url='/accounts/login/')
def laboratory_edit(request, lab_id):
    lab = get_object_or_404(Laboratory, lab_id=lab_id)
    if request.method == 'POST':
        lab.name = request.POST.get('name', lab.name)
        lab.accreditation = request.POST.get('accreditation', lab.accreditation)
        hospital_id = request.POST.get('hospital_id', '')
        if hospital_id:
            lab.hospital = Hospital.objects.filter(hospital_id=hospital_id).first()
        elif 'clear_hospital' in request.POST:
            lab.hospital = None
        lab.save()
        messages.success(request, f'Laboratory "{lab.name}" updated.')
        return redirect('laboratory_detail', lab_id=lab_id)
    hospitals = Hospital.objects.order_by('name')
    return render(request, 'healthcare/laboratory_edit.html', {'lab': lab, 'hospitals': hospitals})


@login_required(login_url='/accounts/login/')
def laboratory_delete(request, lab_id):
    lab = get_object_or_404(Laboratory, lab_id=lab_id)
    if request.method == 'POST':
        name = lab.name
        lab.delete()
        messages.success(request, f'Laboratory "{name}" deleted.')
        return redirect('laboratory_list')
    hospitals = Hospital.objects.order_by('name')
    return render(request, 'healthcare/laboratory_edit.html', {
        'lab': lab, 'hospitals': hospitals, 'confirm_delete': True,
    })


# ==================== INSURANCE PROVIDER EDIT / DELETE ====================

@login_required(login_url='/accounts/login/')
def insurance_edit(request, provider_id):
    provider = get_object_or_404(InsuranceProvider, provider_id=provider_id)
    if request.method == 'POST':
        provider.name = request.POST.get('name', provider.name)
        provider.license_number = request.POST.get('license_number', provider.license_number)
        provider.save()
        messages.success(request, f'Insurance provider "{provider.name}" updated.')
        return redirect('insurance_detail', provider_id=provider_id)
    return render(request, 'healthcare/insurance_edit.html', {'provider': provider})


@login_required(login_url='/accounts/login/')
def insurance_delete(request, provider_id):
    provider = get_object_or_404(InsuranceProvider, provider_id=provider_id)
    if request.method == 'POST':
        name = provider.name
        provider.delete()
        messages.success(request, f'Insurance provider "{name}" deleted.')
        return redirect('insurance_list')
    return render(request, 'healthcare/insurance_edit.html', {'provider': provider, 'confirm_delete': True})


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


# ==================== RECORD REPORT ====================

@login_required(login_url='/accounts/login/')
def record_report(request, record_id):
    """Summary report for a single medical record."""
    record = get_object_or_404(
        MedicalRecord.objects.select_related('patient__user', 'hospital', 'blockchain_tx'),
        record_id=record_id,
    )
    permissions = AccessPermission.objects.filter(record=record).order_by('-created_at')
    audit_logs = AuditLog.objects.filter(record=record).order_by('-timestamp')
    return render(request, 'healthcare/record_report.html', {
        'record': record,
        'permissions': permissions,
        'audit_logs': audit_logs,
        'active_permissions': permissions.filter(is_active=True).count(),
        'generated_at': timezone.now(),
        'generated_by': request.user.get_full_name() or request.user.username,
    })


@login_required(login_url='/accounts/login/')
def record_print_report(request, record_id):
    """Standalone printable document for a medical record."""
    record = get_object_or_404(
        MedicalRecord.objects.select_related('patient__user', 'hospital', 'blockchain_tx'),
        record_id=record_id,
    )
    permissions = AccessPermission.objects.filter(record=record).order_by('-created_at')
    audit_logs = AuditLog.objects.filter(record=record).order_by('-timestamp')[:30]
    return render(request, 'healthcare/record_print_report.html', {
        'record': record,
        'permissions': permissions,
        'audit_logs': audit_logs,
        'active_permissions': permissions.filter(is_active=True).count(),
        'generated_at': timezone.now(),
        'generated_by': request.user.get_full_name() or request.user.username,
    })


# ==================== HOSPITAL REPORT ====================

@login_required(login_url='/accounts/login/')
def hospital_report(request, hospital_id):
    """Printable hospital report — activity, records, labs, and compliance summary."""
    hospital = get_object_or_404(Hospital, hospital_id=hospital_id)
    records = MedicalRecord.objects.filter(hospital=hospital).select_related(
        'patient__user', 'blockchain_tx'
    ).order_by('-created_at')
    labs = Laboratory.objects.filter(hospital=hospital).order_by('name')
    audit_logs = AuditLog.objects.filter(record__hospital=hospital).order_by('-timestamp')[:50]

    total_records = records.count()
    unique_patients = records.values('patient').distinct().count()

    type_counts = {}
    for r in records:
        label = r.get_record_type_display()
        type_counts[label] = type_counts.get(label, 0) + 1
    record_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / total_records * 100) if total_records else 0}
        for label, count in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    return render(request, 'healthcare/hospital_report.html', {
        'hospital': hospital,
        'records': records,
        'labs': labs,
        'audit_logs': audit_logs,
        'record_breakdown': record_breakdown,
        'total_records': total_records,
        'unique_patients': unique_patients,
        'generated_at': timezone.now(),
    })


# ==================== LABORATORY REPORT ====================

@login_required(login_url='/accounts/login/')
def laboratory_report(request, lab_id):
    """Printable lab report — lab result records from the parent hospital, permissions."""
    lab = get_object_or_404(Laboratory.objects.select_related('hospital'), lab_id=lab_id)

    # Lab results are records of type LAB_RESULT from this lab's hospital
    lab_records = MedicalRecord.objects.none()
    hospital_records = MedicalRecord.objects.none()
    if lab.hospital:
        hospital_records = MedicalRecord.objects.filter(
            hospital=lab.hospital
        ).select_related('patient__user').order_by('-created_at')
        lab_records = hospital_records.filter(record_type='LAB_RESULT')

    # Permissions where a lab grantee name contains this lab's name (approximate match)
    permissions = AccessPermission.objects.filter(
        grantee_type='LAB', grantee__icontains=lab.name
    ).select_related('record', 'grantor__user').order_by('-created_at')

    total_lab_results = lab_records.count()
    total_hospital_records = hospital_records.count()

    return render(request, 'healthcare/laboratory_report.html', {
        'lab': lab,
        'lab_records': lab_records[:100],
        'permissions': permissions,
        'total_lab_results': total_lab_results,
        'total_hospital_records': total_hospital_records,
        'generated_at': timezone.now(),
    })


# ==================== INSURANCE REPORT ====================

@login_required(login_url='/accounts/login/')
def insurance_report(request, provider_id):
    """Printable insurance provider report — claims, permissions, access history."""
    provider = get_object_or_404(InsuranceProvider, provider_id=provider_id)

    # Permissions granted to this insurance provider (name match)
    permissions = AccessPermission.objects.filter(
        grantee_type='INSURANCE', grantee__icontains=provider.name
    ).select_related('record__patient__user', 'grantor__user').order_by('-created_at')

    # Insurance-type medical records (claims)
    claims = MedicalRecord.objects.filter(
        record_type='INSURANCE', is_active=True
    ).select_related('patient__user', 'hospital').order_by('-created_at')

    total_permissions = permissions.count()
    active_permissions = permissions.filter(is_active=True).count()

    return render(request, 'healthcare/insurance_report.html', {
        'provider': provider,
        'permissions': permissions,
        'claims': claims,
        'total_permissions': total_permissions,
        'active_permissions': active_permissions,
        'generated_at': timezone.now(),
    })


# ==================== AUDIT / COMPLIANCE REPORT ====================

@login_required(login_url='/accounts/login/')
def audit_compliance_report(request):
    """System-wide audit and compliance report with optional date-range filter."""
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    actor_type_filter = request.GET.get('actor_type', '').strip()

    qs = AuditLog.objects.select_related('record__patient__user', 'record__hospital').order_by('-timestamp')
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)
    if actor_type_filter:
        qs = qs.filter(actor_type=actor_type_filter)

    logs = qs[:200]

    action_counts = {}
    actor_type_counts = {}
    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        actor_type_counts[log.actor_type] = actor_type_counts.get(log.actor_type, 0) + 1

    total_logs = len(logs)
    denied_count = action_counts.get('ACCESS_DENIED', 0)

    action_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / total_logs * 100) if total_logs else 0}
        for label, count in sorted(action_counts.items(), key=lambda x: -x[1])
    ]
    actor_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / total_logs * 100) if total_logs else 0}
        for label, count in sorted(actor_type_counts.items(), key=lambda x: -x[1])
    ]

    return render(request, 'healthcare/audit_compliance_report.html', {
        'logs': logs,
        'action_breakdown': action_breakdown,
        'actor_breakdown': actor_breakdown,
        'total_logs': total_logs,
        'denied_count': denied_count,
        'date_from': date_from,
        'date_to': date_to,
        'actor_type_filter': actor_type_filter,
        'generated_at': timezone.now(),
    })


# ==================== SYSTEM OVERVIEW REPORT ====================

@login_required(login_url='/accounts/login/')
def system_overview_report(request):
    """Platform-wide summary report — entity counts, blockchain stats, activity."""
    # Healthcare counts
    patient_count = Patient.objects.filter(is_active=True).count()
    hospital_count = Hospital.objects.count()
    lab_count = Laboratory.objects.count()
    insurance_count = InsuranceProvider.objects.count()
    record_count = MedicalRecord.objects.filter(is_active=True).count()
    active_permissions = AccessPermission.objects.filter(is_active=True).count()
    audit_count = AuditLog.objects.count()

    # Blockchain counts
    network_count = BlockchainNetwork.objects.filter(is_active=True).count()
    block_count = Block.objects.count()
    tx_count = Transaction.objects.count()
    rollup_count = RollupBatch.objects.count()

    # Record type breakdown
    all_records = MedicalRecord.objects.filter(is_active=True)
    type_counts = {}
    for r in all_records:
        label = r.get_record_type_display()
        type_counts[label] = type_counts.get(label, 0) + 1
    record_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / record_count * 100) if record_count else 0}
        for label, count in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    # Recent activity
    recent_records = MedicalRecord.objects.select_related('patient__user', 'hospital').order_by('-created_at')[:10]
    recent_logs = AuditLog.objects.select_related('record').order_by('-timestamp')[:10]
    recent_txs = Transaction.objects.order_by('-timestamp')[:10]

    return render(request, 'healthcare/system_overview_report.html', {
        'patient_count': patient_count,
        'hospital_count': hospital_count,
        'lab_count': lab_count,
        'insurance_count': insurance_count,
        'record_count': record_count,
        'active_permissions': active_permissions,
        'audit_count': audit_count,
        'network_count': network_count,
        'block_count': block_count,
        'tx_count': tx_count,
        'rollup_count': rollup_count,
        'record_breakdown': record_breakdown,
        'recent_records': recent_records,
        'recent_logs': recent_logs,
        'recent_txs': recent_txs,
        'generated_at': timezone.now(),
    })


# ==================== AUDIT COMPLIANCE PRINT REPORT ====================

@login_required(login_url='/accounts/login/')
def audit_compliance_print_report(request):
    """Standalone printable audit & compliance report."""
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    actor_type_filter = request.GET.get('actor_type', '').strip()

    qs = AuditLog.objects.select_related('record__patient__user', 'record__hospital').order_by('-timestamp')
    if date_from:
        qs = qs.filter(timestamp__date__gte=date_from)
    if date_to:
        qs = qs.filter(timestamp__date__lte=date_to)
    if actor_type_filter:
        qs = qs.filter(actor_type=actor_type_filter)

    logs = qs[:500]
    total_logs = len(logs)

    action_counts = {}
    actor_type_counts = {}
    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
        actor_type_counts[log.actor_type] = actor_type_counts.get(log.actor_type, 0) + 1

    denied_count = action_counts.get('ACCESS_DENIED', 0)
    action_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / total_logs * 100) if total_logs else 0}
        for label, count in sorted(action_counts.items(), key=lambda x: -x[1])
    ]
    actor_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / total_logs * 100) if total_logs else 0}
        for label, count in sorted(actor_type_counts.items(), key=lambda x: -x[1])
    ]

    return render(request, 'healthcare/audit_compliance_print_report.html', {
        'logs': logs,
        'action_breakdown': action_breakdown,
        'actor_breakdown': actor_breakdown,
        'total_logs': total_logs,
        'denied_count': denied_count,
        'date_from': date_from,
        'date_to': date_to,
        'actor_type_filter': actor_type_filter,
        'generated_at': timezone.now(),
        'generated_by': request.user.get_full_name() or request.user.username,
    })


# ==================== SYSTEM OVERVIEW PRINT REPORT ====================

@login_required(login_url='/accounts/login/')
def system_overview_print_report(request):
    """Standalone printable platform-wide summary report."""
    patient_count = Patient.objects.filter(is_active=True).count()
    hospital_count = Hospital.objects.count()
    lab_count = Laboratory.objects.count()
    insurance_count = InsuranceProvider.objects.count()
    record_count = MedicalRecord.objects.filter(is_active=True).count()
    active_permissions = AccessPermission.objects.filter(is_active=True).count()
    audit_count = AuditLog.objects.count()

    network_count = BlockchainNetwork.objects.filter(is_active=True).count()
    block_count = Block.objects.count()
    tx_count = Transaction.objects.count()
    rollup_count = RollupBatch.objects.count()

    all_records = MedicalRecord.objects.filter(is_active=True)
    type_counts = {}
    for r in all_records:
        label = r.get_record_type_display()
        type_counts[label] = type_counts.get(label, 0) + 1
    record_breakdown = [
        {'label': label, 'count': count, 'pct': round(count / record_count * 100) if record_count else 0}
        for label, count in sorted(type_counts.items(), key=lambda x: -x[1])
    ]

    recent_records = MedicalRecord.objects.select_related('patient__user', 'hospital').order_by('-created_at')[:15]
    recent_logs = AuditLog.objects.select_related('record').order_by('-timestamp')[:15]
    recent_txs = Transaction.objects.order_by('-timestamp')[:15]

    return render(request, 'healthcare/system_overview_print_report.html', {
        'patient_count': patient_count,
        'hospital_count': hospital_count,
        'lab_count': lab_count,
        'insurance_count': insurance_count,
        'record_count': record_count,
        'active_permissions': active_permissions,
        'audit_count': audit_count,
        'network_count': network_count,
        'block_count': block_count,
        'tx_count': tx_count,
        'rollup_count': rollup_count,
        'record_breakdown': record_breakdown,
        'recent_records': recent_records,
        'recent_logs': recent_logs,
        'recent_txs': recent_txs,
        'generated_at': timezone.now(),
        'generated_by': request.user.get_full_name() or request.user.username,
    })


# ==================== REPORTS HUB ====================

@login_required(login_url='/accounts/login/')
def reports_hub(request):
    """Central hub listing all available reports."""
    patient_count = Patient.objects.filter(is_active=True).count()
    hospital_count = Hospital.objects.count()
    lab_count = Laboratory.objects.count()
    insurance_count = InsuranceProvider.objects.count()
    record_count = MedicalRecord.objects.filter(is_active=True).count()
    audit_count = AuditLog.objects.count()
    return render(request, 'healthcare/reports_hub.html', {
        'patient_count': patient_count,
        'hospital_count': hospital_count,
        'lab_count': lab_count,
        'insurance_count': insurance_count,
        'record_count': record_count,
        'audit_count': audit_count,
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
