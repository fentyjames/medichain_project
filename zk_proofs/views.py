"""
MediChain ZK Proof Views
Template rendering + API for ZK operations
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .zk_service import MerkleTreeService, ZKProofService

# ==================== TEMPLATE VIEWS ====================

@login_required(login_url='/accounts/login/')
def zk_dashboard(request):
    """ZK proofs dashboard"""
    return render(request, 'zk_proofs/dashboard.html')


@login_required(login_url='/accounts/login/')
def zk_generate(request):
    """Generate ZK proof form"""
    if request.method == 'POST':
        inputs = [i.strip() for i in request.POST.get('inputs', '').split('\n') if i.strip()]
        public_output = request.POST.get('public_output', '')
        proof_type = request.POST.get('proof_type', 'zk_snark')

        zk_service = ZKProofService(proof_type)
        proof = zk_service.generate_proof(inputs, public_output)

        messages.success(request, 'ZK Proof generated successfully!')
        messages.info(request, f'Proof: {str(proof)[:120]}…')
        return redirect('zk_dashboard')
    return render(request, 'zk_proofs/generate.html')


@login_required(login_url='/accounts/login/')
def zk_verify_page(request):
    """Verify ZK proof form"""
    if request.method == 'POST':
        proof = request.POST.get('proof', '')
        public_output = request.POST.get('public_output', '')
        expected_inputs = [i.strip() for i in request.POST.get('expected_inputs', '').split('\n') if i.strip()]
        proof_type = request.POST.get('proof_type', 'zk_snark')

        zk_service = ZKProofService(proof_type)
        is_valid = zk_service.verify_proof(proof, public_output, expected_inputs)

        if is_valid:
            messages.success(request, 'ZK Proof is VALID — commitment verified successfully.')
        else:
            messages.error(request, 'ZK Proof is INVALID — commitment does not match.')
        return redirect('zk_dashboard')
    return render(request, 'zk_proofs/verify.html')


@login_required(login_url='/accounts/login/')
def zk_range(request):
    """Range proof form"""
    if request.method == 'POST':
        try:
            value = int(request.POST.get('value', 0))
            min_val = int(request.POST.get('min', 0))
            max_val = int(request.POST.get('max', 100))
        except ValueError:
            messages.error(request, 'Value, min, and max must all be integers.')
            return redirect('zk_range')

        zk_service = ZKProofService()
        proof = zk_service.create_range_proof(value, min_val, max_val)
        is_valid = zk_service.verify_range_proof(proof, min_val, max_val)

        if is_valid:
            messages.success(request, f'Range proof verified: value is within [{min_val}, {max_val}]')
        else:
            messages.error(request, 'Range proof verification failed')
        return redirect('zk_dashboard')
    return render(request, 'zk_proofs/range.html')


# ==================== API VIEWS ====================

class GenerateProofView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        inputs = request.data.get('inputs', [])
        public_output = request.data.get('public_output', '')
        proof_type = request.data.get('proof_type', 'zk_snark')

        zk_service = ZKProofService(proof_type)
        proof = zk_service.generate_proof(inputs, public_output)

        return Response({'proof': proof, 'proof_type': proof_type, 'status': 'generated'})


class VerifyProofView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        proof = request.data.get('proof', '')
        public_output = request.data.get('public_output', '')
        expected_inputs = request.data.get('expected_inputs', [])
        proof_type = request.data.get('proof_type', 'zk_snark')

        zk_service = ZKProofService(proof_type)
        is_valid = zk_service.verify_proof(proof, public_output, expected_inputs)

        return Response({'is_valid': is_valid, 'proof_type': proof_type})


class RangeProofView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        action = request.data.get('action', 'generate')
        zk_service = ZKProofService()

        if action == 'generate':
            value = request.data.get('value', 0)
            min_val = request.data.get('min', 0)
            max_val = request.data.get('max', 100)
            proof = zk_service.create_range_proof(value, min_val, max_val)
            return Response({'proof': proof, 'action': 'generate'})

        elif action == 'verify':
            proof = request.data.get('proof', '')
            min_val = request.data.get('min', 0)
            max_val = request.data.get('max', 100)
            is_valid = zk_service.verify_range_proof(proof, min_val, max_val)
            return Response({'is_valid': is_valid, 'action': 'verify'})

        return Response({'error': 'Invalid action'}, status=400)
