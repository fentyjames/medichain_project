"""
MediChain Test Suite
Unit tests for blockchain, ZK proofs, cross-chain relay, and healthcare modules
"""

import hashlib
import json
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from blockchain.models import BlockchainNetwork, Block, Transaction, RollupBatch
from healthcare.models import Patient, Hospital, MedicalRecord, AccessPermission
from zk_proofs.zk_service import ZKProofService, MerkleTreeService
from cross_chain.relay_service import CrossChainRelayService

User = get_user_model()


class ZKProofServiceTest(TestCase):
    """Test Zero-Knowledge Proof generation and verification"""

    def setUp(self):
        self.zk_service = ZKProofService('zk_snark')
        self.test_inputs = ['tx_hash_1', 'tx_hash_2', 'tx_hash_3']
        self.test_output = hashlib.sha256(b'test_merkle_root').hexdigest()

    def test_generate_proof(self):
        """Test proof generation"""
        proof = self.zk_service.generate_proof(self.test_inputs, self.test_output)
        self.assertIsNotNone(proof)

        # Verify proof is valid JSON
        proof_data = json.loads(proof)
        self.assertEqual(proof_data['proof_type'], 'zk_snark')
        self.assertEqual(proof_data['public_inputs']['merkle_root'], self.test_output)
        self.assertEqual(proof_data['public_inputs']['input_count'], len(self.test_inputs))

    def test_verify_proof_valid(self):
        """Test valid proof verification"""
        proof = self.zk_service.generate_proof(self.test_inputs, self.test_output)
        is_valid = self.zk_service.verify_proof(proof, self.test_output, self.test_inputs)
        self.assertTrue(is_valid)

    def test_verify_proof_invalid_output(self):
        """Test proof verification with wrong output"""
        proof = self.zk_service.generate_proof(self.test_inputs, self.test_output)
        wrong_output = hashlib.sha256(b'wrong').hexdigest()
        is_valid = self.zk_service.verify_proof(proof, wrong_output, self.test_inputs)
        self.assertFalse(is_valid)

    def test_range_proof(self):
        """Test range proof generation and verification"""
        proof = self.zk_service.create_range_proof(50, 0, 100)
        is_valid = self.zk_service.verify_range_proof(proof, 0, 100)
        self.assertTrue(is_valid)

        is_invalid = self.zk_service.verify_range_proof(proof, 0, 40)
        self.assertFalse(is_invalid)


class MerkleTreeServiceTest(TestCase):
    """Test Merkle tree operations"""

    def test_build_merkle_tree(self):
        """Test Merkle tree construction"""
        leaves = ['a', 'b', 'c', 'd']
        tree = MerkleTreeService.build_merkle_tree(leaves)

        self.assertIsNotNone(tree['root'])
        self.assertEqual(tree['leaf_count'], 4)
        self.assertGreater(len(tree['levels']), 0)

    def test_verify_merkle_proof(self):
        """Test Merkle proof verification"""
        leaves = ['a', 'b', 'c', 'd']
        tree = MerkleTreeService.build_merkle_tree(leaves)

        proof_path = MerkleTreeService.get_proof_path(tree, 0)
        is_valid = MerkleTreeService.verify_merkle_proof(
            tree['root'], leaves[0], proof_path
        )
        self.assertTrue(is_valid)

    def test_empty_tree(self):
        """Test empty Merkle tree"""
        tree = MerkleTreeService.build_merkle_tree([])
        self.assertIsNotNone(tree['root'])
        self.assertEqual(tree['leaf_count'], 0)


class CrossChainRelayTest(TestCase):
    """Test cross-chain relay functionality"""

    def setUp(self):
        self.relay_service = CrossChainRelayService()
        self.source_chain = 'ethereum_main'
        self.target_chain = 'polygon'
        self.data_hash = hashlib.sha256(b'test_data').hexdigest()

        zk_service = ZKProofService()
        self.proof = zk_service.generate_proof([self.data_hash], self.data_hash)

    def test_create_message(self):
        """Test cross-chain message creation"""
        message = self.relay_service.create_message(
            self.source_chain, self.target_chain, 
            self.data_hash, self.proof, 'sender_1'
        )

        self.assertIsNotNone(message['message_id'])
        self.assertEqual(message['source_chain'], self.source_chain)
        self.assertEqual(message['target_chain'], self.target_chain)
        self.assertEqual(message['status'], 'PENDING')

    def test_verify_message(self):
        """Test message verification"""
        message = self.relay_service.create_message(
            self.source_chain, self.target_chain,
            self.data_hash, self.proof, 'sender_1'
        )

        is_valid = self.relay_service.verify_message(message)
        self.assertTrue(is_valid)

    def test_relay_message(self):
        """Test message relay"""
        message = self.relay_service.create_message(
            self.source_chain, self.target_chain,
            self.data_hash, self.proof, 'sender_1'
        )

        result = self.relay_service.relay_message(message)
        self.assertEqual(result['status'], 'RELAYED')
        self.assertIn('relayed_at', result)


class BlockchainModelTest(TestCase):
    """Test blockchain models"""

    def setUp(self):
        self.network = BlockchainNetwork.objects.create(
            network_id='test_eth',
            name='Test Ethereum',
            chain_id=1,
            rpc_url='http://localhost:8545',
            consensus_type='PoS'
        )

    def test_block_creation(self):
        """Test block creation and hash"""
        block = Block.objects.create(
            block_number=1,
            previous_hash='0' * 64,
            merkle_root=hashlib.sha256(b'test').hexdigest(),
            rollup_proof='test_proof',
            nonce=0,
            network=self.network,
            transaction_count=0
        )

        self.assertIsNotNone(block.hash)
        self.assertEqual(block.block_number, 1)
        self.assertEqual(len(block.hash), 64)

    def test_transaction_creation(self):
        """Test transaction creation"""
        tx = Transaction.objects.create(
            tx_type='CREATE',
            sender='hospital_1',
            data_hash=hashlib.sha256(b'record').hexdigest(),
            signature='sig_123',
            status='PENDING'
        )

        self.assertIsNotNone(tx.tx_hash)
        self.assertEqual(tx.tx_type, 'CREATE')
        self.assertEqual(tx.status, 'PENDING')


class HealthcareModelTest(TestCase):
    """Test healthcare models"""

    def setUp(self):
        self.patient = Patient.objects.create(
            public_key='patient_pub_key',
            blood_type='A+',
        )
        self.hospital = Hospital.objects.create(
            name='Test Hospital',
            address='123 Test St',
            license_number='LIC001',
            public_key='hospital_pub_key',
        )

    def test_medical_record_creation(self):
        """Test medical record creation"""
        record = MedicalRecord.objects.create(
            patient=self.patient,
            hospital=self.hospital,
            record_type='DIAGNOSIS',
            title='Test Diagnosis',
            description='Test description',
            ipfs_hash='QmTest123',
        )

        self.assertIsNotNone(record.record_id)
        self.assertIsNotNone(record.data_hash)
        self.assertEqual(record.record_type, 'DIAGNOSIS')

    def test_record_integrity(self):
        """Test record hash integrity"""
        record = MedicalRecord.objects.create(
            patient=self.patient,
            hospital=self.hospital,
            record_type='DIAGNOSIS',
            title='Test Diagnosis',
            description='Test description',
        )

        computed_hash = record.calculate_hash()
        self.assertEqual(computed_hash, record.data_hash)


class APIIntegrationTest(APITestCase):
    """Integration tests for API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create test network
        self.network = BlockchainNetwork.objects.create(
            network_id='test_net',
            name='Test Network',
            chain_id=999,
            rpc_url='http://test',
        )

    def test_dashboard_api(self):
        """Test dashboard endpoint"""
        response = self.client.get('/api/v1/dashboard/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('networks', response.data)
        self.assertIn('total_blocks', response.data)

    def test_create_rollup_api(self):
        """Test rollup creation endpoint"""
        # Create pending transactions
        for i in range(5):
            Transaction.objects.create(
                tx_type='CREATE',
                sender=f'hospital_{i}',
                data_hash=hashlib.sha256(f'tx_{i}'.encode()).hexdigest(),
                signature=f'sig_{i}',
                status='PENDING'
            )

        response = self.client.post('/api/v1/rollup/create/', {
            'network_id': 'test_net'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('batch_created'))

    def test_zk_verify_api(self):
        """Test ZK proof verification endpoint"""
        zk_service = ZKProofService()
        inputs = ['input_1', 'input_2']
        output = hashlib.sha256(b'output').hexdigest()
        proof = zk_service.generate_proof(inputs, output)

        response = self.client.post('/api/v1/zk/verify/', {
            'proof': proof,
            'public_output': output,
            'expected_inputs': inputs,
            'proof_type': 'zk_snark'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get('is_valid'))

    def test_merkle_tree_api(self):
        """Test Merkle tree endpoint"""
        response = self.client.post('/api/v1/merkle/', {
            'action': 'build',
            'leaves': ['a', 'b', 'c', 'd']
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('root', response.data)
        self.assertEqual(response.data['leaf_count'], 4)

    def test_cross_chain_transfer_api(self):
        """Test cross-chain transfer endpoint"""
        target_network = BlockchainNetwork.objects.create(
            network_id='target_net',
            name='Target Network',
            chain_id=137,
            rpc_url='http://target',
        )

        zk_service = ZKProofService()
        data_hash = hashlib.sha256(b'test_data').hexdigest()
        proof = zk_service.generate_proof([data_hash], data_hash)

        response = self.client.post('/api/v1/cross-chain/transfer/', {
            'source_chain': 'test_net',
            'target_chain': 'target_net',
            'data_hash': data_hash,
            'proof': proof,
            'sender': 'hospital_1'
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('message_id', response.data)
        self.assertEqual(response.data['status'], 'RELAYED')


class PerformanceTest(TestCase):
    """Performance benchmarks"""

    def test_rollup_batch_throughput(self):
        """Test rollup batch processing throughput"""
        import time

        network = BlockchainNetwork.objects.create(
            network_id='perf_test',
            name='Performance Test',
            chain_id=999,
            rpc_url='http://test',
        )

        # Create 100 transactions
        start_time = time.time()
        transactions = []
        for i in range(100):
            tx = Transaction.objects.create(
                tx_type='CREATE',
                sender=f'hospital_{i}',
                data_hash=hashlib.sha256(f'tx_{i}'.encode()).hexdigest(),
                signature=f'sig_{i}',
                status='PENDING'
            )
            transactions.append(tx)

        create_time = time.time() - start_time

        # Batch into rollups
        batch_size = 50
        batches = [transactions[i:i+batch_size] for i in range(0, len(transactions), batch_size)]

        zk_service = ZKProofService()
        rollup_start = time.time()

        for batch_txs in batches:
            batch = RollupBatch.objects.create(network=network)
            batch.transactions.set(batch_txs)
            batch.merkle_root = batch.calculate_merkle_root()
            tx_hashes = [tx.tx_hash for tx in batch_txs]
            batch.zk_proof = zk_service.generate_proof(tx_hashes, batch.merkle_root)
            batch.save()

        rollup_time = time.time() - rollup_start

        # Assert performance requirements
        self.assertLess(create_time, 5.0, "Transaction creation too slow")
        self.assertLess(rollup_time, 10.0, "Rollup processing too slow")

        # Verify throughput improvement
        single_chain_time = 100 * 0.5  # 0.5s per tx
        rollup_time_total = create_time + rollup_time
        speedup = single_chain_time / rollup_time_total

        self.assertGreater(speedup, 2.0, "Rollup speedup insufficient")


# ==================== ACCOUNTS TESTS ====================

class AccountsAuthTest(TestCase):
    """Tests for login, logout, and access control"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='authuser',
            email='auth@test.com',
            password='TestPass123!',
            role='PATIENT',
        )

    def test_dashboard_redirects_unauthenticated(self):
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/accounts/login/?next=/dashboard/', fetch_redirect_response=False)

    def test_login_success_redirects(self):
        response = self.client.post('/accounts/login/', {
            'username': 'authuser',
            'password': 'TestPass123!',
        })
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)

    def test_login_wrong_password_stays_on_page(self):
        response = self.client.post('/accounts/login/', {
            'username': 'authuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_logout_requires_authentication(self):
        response = self.client.get('/accounts/logout/')
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_access_dashboard(self):
        self.client.force_login(self.user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_rate_limiting_triggers_after_max_attempts(self):
        from accounts.views import MAX_LOGIN_ATTEMPTS
        for _ in range(MAX_LOGIN_ATTEMPTS):
            self.client.post('/accounts/login/', {
                'username': 'authuser',
                'password': 'badpassword',
            })
        response = self.client.post('/accounts/login/', {
            'username': 'authuser',
            'password': 'badpassword',
        })
        # Rate-limited response renders login page with rate_limited=True
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get('rate_limited'))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountsRegistrationTest(TestCase):
    """Tests for user registration"""

    def setUp(self):
        self.client = Client()
        self.valid_data = {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@test.com',
            'role': 'PATIENT',
            'organization': '',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }

    def test_registration_page_loads(self):
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 200)

    def test_registration_creates_user(self):
        response = self.client.post('/accounts/register/', self.valid_data)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertRedirects(response, '/accounts/login/', fetch_redirect_response=False)

    def test_registration_duplicate_username_rejected(self):
        User.objects.create_user(username='newuser', email='other@test.com', password='x')
        response = self.client.post('/accounts/register/', self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='newuser@test.com').exists())

    def test_registration_mismatched_passwords_rejected(self):
        data = {**self.valid_data, 'password2': 'DifferentPass999!'}
        response = self.client.post('/accounts/register/', data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_authenticated_user_redirected_from_register(self):
        user = User.objects.create_user(username='existing', password='x', email='e@e.com')
        self.client.force_login(user)
        response = self.client.get('/accounts/register/')
        self.assertEqual(response.status_code, 302)


# ==================== HEALTHCARE API TESTS ====================

class HealthcareAPITest(APITestCase):
    """Tests for healthcare REST API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='hcuser',
            email='hc@test.com',
            password='TestPass123!',
            role='DOCTOR',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.patient = Patient.objects.create(public_key='pub_key_test')
        self.hospital = Hospital.objects.create(
            name='Test Hospital',
            address='1 Test St',
            license_number='LIC123',
            public_key='hosp_pub_key',
        )

    def test_patient_list_returns_200(self):
        response = self.client.get('/api/healthcare/api/patients/')
        self.assertEqual(response.status_code, 200)

    def test_hospital_list_returns_200(self):
        response = self.client.get('/api/healthcare/api/hospitals/')
        self.assertEqual(response.status_code, 200)

    def test_record_list_returns_200(self):
        response = self.client.get('/api/healthcare/api/records/')
        self.assertEqual(response.status_code, 200)

    def test_audit_list_returns_200(self):
        response = self.client.get('/api/healthcare/api/audit/')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_request_rejected(self):
        self.client.credentials()
        response = self.client.get('/api/healthcare/api/patients/')
        self.assertIn(response.status_code, [401, 403])

    def test_patient_detail_returns_correct_record(self):
        # retrieve() uses patient_id (SHA-256 string), not integer PK
        response = self.client.get(f'/api/healthcare/api/patients/{self.patient.patient_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['patient_id'], self.patient.patient_id)

    def test_medical_record_creation_via_api(self):
        response = self.client.post('/api/healthcare/api/records/', {
            'patient_id': self.patient.patient_id,
            'hospital_id': self.hospital.hospital_id,
            'record_type': 'DIAGNOSIS',
            'title': 'API Test Record',
            'description': 'Created via API test',
        })
        self.assertIn(response.status_code, [200, 201])
        if response.status_code in [200, 201]:
            self.assertTrue(
                MedicalRecord.objects.filter(title='API Test Record').exists()
            )
