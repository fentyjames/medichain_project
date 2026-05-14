"""
Management command: seed_data
Populates every database table with sample records for development/testing.
Usage: python manage.py seed_data [--clear]
"""

import hashlib
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import UserProfile
from blockchain.models import (
    Block,
    BlockchainNetwork,
    CrossChainMessage,
    RollupBatch,
    SmartContract,
    Transaction,
    ValidatorNode,
)
from healthcare.models import (
    AccessPermission,
    AuditLog,
    Hospital,
    InsuranceProvider,
    Laboratory,
    MedicalRecord,
    Patient,
)

User = get_user_model()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


class Command(BaseCommand):
    help = "Seed the database with sample data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            self._clear()

        self.stdout.write("Seeding data...")

        networks = self._seed_blockchain_networks()
        blocks = self._seed_blocks(networks)
        txs = self._seed_transactions(blocks)
        self._seed_rollup_batches(networks, txs)
        self._seed_cross_chain_messages(networks)
        self._seed_validator_nodes(networks)
        self._seed_smart_contracts(networks)

        users, profiles = self._seed_users()
        hospitals = self._seed_hospitals(networks)
        labs = self._seed_laboratories(hospitals)
        insurers = self._seed_insurance_providers()
        patients = self._seed_patients(users)
        records = self._seed_medical_records(patients, hospitals, txs)
        self._seed_access_permissions(patients, records)
        self._seed_audit_logs(records)

        self.stdout.write(self.style.SUCCESS("Done! Database seeded successfully."))

    # ------------------------------------------------------------------
    # clear
    # ------------------------------------------------------------------

    def _clear(self):
        AuditLog.objects.all().delete()
        AccessPermission.objects.all().delete()
        MedicalRecord.objects.all().delete()
        Patient.objects.all().delete()
        InsuranceProvider.objects.all().delete()
        Laboratory.objects.all().delete()
        Hospital.objects.all().delete()
        RollupBatch.objects.all().delete()
        CrossChainMessage.objects.all().delete()
        Transaction.objects.all().delete()
        Block.objects.all().delete()
        ValidatorNode.objects.all().delete()
        SmartContract.objects.all().delete()
        BlockchainNetwork.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

    # ------------------------------------------------------------------
    # blockchain
    # ------------------------------------------------------------------

    def _seed_blockchain_networks(self):
        data = [
            {
                "network_id": "medichain-mainnet",
                "name": "MediChain Mainnet",
                "chain_id": 8001,
                "rpc_url": "https://rpc.medichain.example/mainnet",
                "consensus_type": "PBFT",
                "is_active": True,
            },
            {
                "network_id": "medichain-testnet",
                "name": "MediChain Testnet",
                "chain_id": 8002,
                "rpc_url": "https://rpc.medichain.example/testnet",
                "consensus_type": "PBFT",
                "is_active": True,
            },
            {
                "network_id": "medichain-devnet",
                "name": "MediChain Devnet",
                "chain_id": 8003,
                "rpc_url": "http://localhost:8545",
                "consensus_type": "PoA",
                "is_active": False,
            },
        ]
        networks = []
        for d in data:
            obj, created = BlockchainNetwork.objects.get_or_create(
                network_id=d["network_id"], defaults=d
            )
            networks.append(obj)
            self._log("BlockchainNetwork", obj.name, created)
        return networks

    def _seed_blocks(self, networks):
        mainnet = networks[0]
        genesis_hash = _sha("genesis_block_medichain")
        blocks_data = [
            {
                "block_number": 1,
                "previous_hash": "0" * 64,
                "merkle_root": _sha("merkle_root_block_1"),
                "rollup_proof": json.dumps({"type": "zk_snark", "proof": _sha("proof_1")}),
                "nonce": 12345,
                "network": mainnet,
                "transaction_count": 2,
            },
            {
                "block_number": 2,
                "previous_hash": genesis_hash,
                "merkle_root": _sha("merkle_root_block_2"),
                "rollup_proof": json.dumps({"type": "zk_snark", "proof": _sha("proof_2")}),
                "nonce": 67890,
                "network": mainnet,
                "transaction_count": 3,
            },
            {
                "block_number": 3,
                "previous_hash": _sha("block_2_hash"),
                "merkle_root": _sha("merkle_root_block_3"),
                "rollup_proof": json.dumps({"type": "zk_stark", "proof": _sha("proof_3")}),
                "nonce": 11111,
                "network": networks[1],
                "transaction_count": 1,
            },
        ]
        blocks = []
        for d in blocks_data:
            obj, created = Block.objects.get_or_create(
                block_number=d["block_number"], defaults=d
            )
            blocks.append(obj)
            self._log("Block", f"#{obj.block_number}", created)
        return blocks

    def _seed_transactions(self, blocks):
        tx_data = [
            {
                "tx_type": "CREATE",
                "sender": "0xPatient001",
                "receiver": "0xHospital001",
                "data_hash": _sha("patient_record_create_001"),
                "signature": _sha("sig_create_001"),
                "nonce": str(uuid.uuid4()),
                "block": blocks[0],
                "status": "CONFIRMED",
                "gas_used": 21000,
            },
            {
                "tx_type": "SHARE",
                "sender": "0xPatient001",
                "receiver": "0xLab001",
                "data_hash": _sha("patient_record_share_001"),
                "signature": _sha("sig_share_001"),
                "nonce": str(uuid.uuid4()),
                "block": blocks[0],
                "status": "CONFIRMED",
                "gas_used": 15000,
            },
            {
                "tx_type": "VERIFY",
                "sender": "0xHospital001",
                "receiver": "0xInsurance001",
                "data_hash": _sha("record_verify_001"),
                "signature": _sha("sig_verify_001"),
                "nonce": str(uuid.uuid4()),
                "block": blocks[1],
                "status": "CONFIRMED",
                "gas_used": 18000,
            },
            {
                "tx_type": "UPDATE",
                "sender": "0xDoctor001",
                "receiver": "0xPatient001",
                "data_hash": _sha("record_update_001"),
                "signature": _sha("sig_update_001"),
                "nonce": str(uuid.uuid4()),
                "block": blocks[1],
                "status": "PENDING",
                "gas_used": 0,
            },
            {
                "tx_type": "ACCESS",
                "sender": "0xLab002",
                "receiver": "0xPatient002",
                "data_hash": _sha("access_request_002"),
                "signature": _sha("sig_access_002"),
                "nonce": str(uuid.uuid4()),
                "block": blocks[2],
                "status": "CONFIRMED",
                "gas_used": 12000,
            },
        ]
        txs = []
        for d in tx_data:
            # tx_hash computed by model.save() — can't match on it for get_or_create
            # Use data_hash as a stable surrogate
            obj = Transaction.objects.filter(data_hash=d["data_hash"]).first()
            if not obj:
                obj = Transaction.objects.create(**d)
                self._log("Transaction", obj.tx_type, True)
            else:
                self._log("Transaction", obj.tx_type, False)
            txs.append(obj)
        return txs

    def _seed_rollup_batches(self, networks, txs):
        batches_data = [
            {
                "merkle_root": _sha("rollup_batch_1_merkle"),
                "zk_proof": json.dumps({"type": "zk_snark", "proof": _sha("rollup_proof_1")}),
                "proof_type": "zk_snark",
                "status": "CONFIRMED",
                "network": networks[0],
                "tx_subset": txs[:2],
            },
            {
                "merkle_root": _sha("rollup_batch_2_merkle"),
                "zk_proof": json.dumps({"type": "zk_snark", "proof": _sha("rollup_proof_2")}),
                "proof_type": "zk_snark",
                "status": "PENDING",
                "network": networks[0],
                "tx_subset": txs[2:4],
            },
            {
                "merkle_root": _sha("rollup_batch_3_merkle"),
                "zk_proof": json.dumps({"type": "zk_stark", "proof": _sha("rollup_proof_3")}),
                "proof_type": "zk_stark",
                "status": "CONFIRMED",
                "network": networks[1],
                "tx_subset": txs[4:],
            },
        ]
        for d in batches_data:
            tx_subset = d.pop("tx_subset")
            existing = RollupBatch.objects.filter(merkle_root=d["merkle_root"]).first()
            if not existing:
                batch = RollupBatch.objects.create(**d)
                batch.transactions.set(tx_subset)
                self._log("RollupBatch", batch.batch_id[:16], True)
            else:
                self._log("RollupBatch", existing.batch_id[:16], False)

    def _seed_cross_chain_messages(self, networks):
        msgs_data = [
            {
                "message_id": _sha("ccm_message_id_001"),
                "source_chain": networks[0],
                "target_chain": networks[1],
                "data_hash": _sha("ccm_payload_001"),
                "proof": json.dumps({"proof": _sha("ccm_proof_001")}),
                "signature": _sha("ccm_sig_001"),
                "nonce": _sha("ccm_nonce_001"),
                "status": "VERIFIED",
            },
            {
                "message_id": _sha("ccm_message_id_002"),
                "source_chain": networks[1],
                "target_chain": networks[0],
                "data_hash": _sha("ccm_payload_002"),
                "proof": json.dumps({"proof": _sha("ccm_proof_002")}),
                "signature": _sha("ccm_sig_002"),
                "nonce": _sha("ccm_nonce_002"),
                "status": "RELAYED",
            },
            {
                "message_id": _sha("ccm_message_id_003"),
                "source_chain": networks[0],
                "target_chain": networks[1],
                "data_hash": _sha("ccm_payload_003"),
                "proof": json.dumps({"proof": _sha("ccm_proof_003")}),
                "signature": _sha("ccm_sig_003"),
                "nonce": _sha("ccm_nonce_003"),
                "status": "PENDING",
            },
        ]
        for d in msgs_data:
            obj, created = CrossChainMessage.objects.get_or_create(
                message_id=d["message_id"], defaults=d
            )
            self._log("CrossChainMessage", obj.status, created)

    def _seed_validator_nodes(self, networks):
        nodes_data = [
            {
                "node_id": _sha("validator_node_alpha"),
                "public_key": _sha("pubkey_alpha"),
                "stake_amount": Decimal("1000.0"),
                "is_active": True,
                "network": networks[0],
            },
            {
                "node_id": _sha("validator_node_beta"),
                "public_key": _sha("pubkey_beta"),
                "stake_amount": Decimal("750.5"),
                "is_active": True,
                "network": networks[0],
            },
            {
                "node_id": _sha("validator_node_gamma"),
                "public_key": _sha("pubkey_gamma"),
                "stake_amount": Decimal("500.0"),
                "is_active": False,
                "network": networks[1],
            },
        ]
        for d in nodes_data:
            obj, created = ValidatorNode.objects.get_or_create(
                node_id=d["node_id"], defaults=d
            )
            self._log("ValidatorNode", obj.node_id[:16], created)

    def _seed_smart_contracts(self, networks):
        contracts_data = [
            {
                "contract_address": "0xMC_RecordRegistry_001",
                "contract_type": "RecordRegistry",
                "abi": [{"name": "createRecord", "type": "function"}],
                "bytecode": _sha("bytecode_record_registry"),
                "network": networks[0],
                "is_active": True,
            },
            {
                "contract_address": "0xMC_AccessControl_001",
                "contract_type": "AccessControl",
                "abi": [{"name": "grantAccess", "type": "function"}],
                "bytecode": _sha("bytecode_access_control"),
                "network": networks[0],
                "is_active": True,
            },
            {
                "contract_address": "0xMC_CrossChainRelay_001",
                "contract_type": "CrossChainRelay",
                "abi": [{"name": "relayMessage", "type": "function"}],
                "bytecode": _sha("bytecode_cross_chain_relay"),
                "network": networks[1],
                "is_active": True,
            },
        ]
        for d in contracts_data:
            obj, created = SmartContract.objects.get_or_create(
                contract_address=d["contract_address"], defaults=d
            )
            self._log("SmartContract", obj.contract_type, created)

    # ------------------------------------------------------------------
    # accounts / users
    # ------------------------------------------------------------------

    def _seed_users(self):
        users_data = [
            {
                "username": "dr_amara_koroma",
                "first_name": "Amara",
                "last_name": "Koroma",
                "email": "amara.koroma@medichain.example",
                "role": "DOCTOR",
                "organization": "Connaught Hospital",
                "is_staff": False,
                "password": "MediChain@2024!",
                "profile": {
                    "specialization": "Cardiology",
                    "license_number": "SL-MED-001",
                    "department": "Cardiology Unit",
                    "years_experience": 12,
                    "bio": "Senior cardiologist with 12 years of experience.",
                },
            },
            {
                "username": "patient_fatima_sesay",
                "first_name": "Fatima",
                "last_name": "Sesay",
                "email": "fatima.sesay@example.com",
                "role": "PATIENT",
                "organization": "",
                "is_staff": False,
                "password": "MediChain@2024!",
                "profile": {
                    "bio": "Patient registered on MediChain.",
                },
            },
            {
                "username": "dr_ibrahim_bangura",
                "first_name": "Ibrahim",
                "last_name": "Bangura",
                "email": "ibrahim.bangura@medichain.example",
                "role": "DOCTOR",
                "organization": "Freetown Medical Centre",
                "is_staff": False,
                "password": "MediChain@2024!",
                "profile": {
                    "specialization": "Internal Medicine",
                    "license_number": "SL-MED-002",
                    "department": "Internal Medicine",
                    "years_experience": 8,
                    "bio": "Internal medicine specialist.",
                },
            },
            {
                "username": "patient_mariama_turay",
                "first_name": "Mariama",
                "last_name": "Turay",
                "email": "mariama.turay@example.com",
                "role": "PATIENT",
                "organization": "",
                "is_staff": False,
                "password": "MediChain@2024!",
                "profile": {
                    "bio": "Patient registered on MediChain.",
                },
            },
            {
                "username": "patient_joseph_conteh",
                "first_name": "Joseph",
                "last_name": "Conteh",
                "email": "joseph.conteh@example.com",
                "role": "PATIENT",
                "organization": "",
                "is_staff": False,
                "password": "MediChain@2024!",
                "profile": {
                    "bio": "Patient registered on MediChain.",
                },
            },
        ]
        users = []
        profiles = []
        for d in users_data:
            profile_data = d.pop("profile")
            password = d.pop("password")
            obj = User.objects.filter(username=d["username"]).first()
            created = False
            if not obj:
                obj = User(**d)
                obj.set_password(password)
                obj.save()
                created = True
            users.append(obj)
            self._log("User", f"{obj.first_name} {obj.last_name} ({obj.role})", created)

            profile, p_created = UserProfile.objects.get_or_create(
                user=obj, defaults=profile_data
            )
            if p_created:
                profiles.append(profile)
                self._log("UserProfile", obj.username, True)

        return users, profiles

    # ------------------------------------------------------------------
    # healthcare
    # ------------------------------------------------------------------

    def _seed_hospitals(self, networks):
        hospitals_data = [
            {
                "name": "Connaught Hospital",
                "address": "Lightfoot Boston Street, Freetown, Sierra Leone",
                "license_number": "SL-HOSP-001",
                "public_key": _sha("pubkey_connaught"),
                "blockchain_network": networks[0],
                "is_verified": True,
            },
            {
                "name": "Freetown Medical Centre",
                "address": "Wilkinson Road, Freetown, Sierra Leone",
                "license_number": "SL-HOSP-002",
                "public_key": _sha("pubkey_freetown_med"),
                "blockchain_network": networks[0],
                "is_verified": True,
            },
            {
                "name": "Bo Government Hospital",
                "address": "Bo, Southern Province, Sierra Leone",
                "license_number": "SL-HOSP-003",
                "public_key": _sha("pubkey_bo_hospital"),
                "blockchain_network": networks[1],
                "is_verified": False,
            },
        ]
        hospitals = []
        for d in hospitals_data:
            obj = Hospital.objects.filter(license_number=d["license_number"]).first()
            created = False
            if not obj:
                obj = Hospital.objects.create(**d)
                created = True
            hospitals.append(obj)
            self._log("Hospital", obj.name, created)
        return hospitals

    def _seed_laboratories(self, hospitals):
        labs_data = [
            {
                "lab_id": _sha("lab_national_ref"),
                "name": "National Reference Laboratory",
                "accreditation": "SL-LAB-001",
                "public_key": _sha("pubkey_lab_001"),
                "hospital": hospitals[0],
            },
            {
                "lab_id": _sha("lab_freetown_path"),
                "name": "Freetown Pathology Lab",
                "accreditation": "SL-LAB-002",
                "public_key": _sha("pubkey_lab_002"),
                "hospital": hospitals[1],
            },
            {
                "lab_id": _sha("lab_bo_diagnostic"),
                "name": "Bo Diagnostic Centre",
                "accreditation": "SL-LAB-003",
                "public_key": _sha("pubkey_lab_003"),
                "hospital": hospitals[2],
            },
        ]
        labs = []
        for d in labs_data:
            obj, created = Laboratory.objects.get_or_create(
                lab_id=d["lab_id"], defaults=d
            )
            labs.append(obj)
            self._log("Laboratory", obj.name, created)
        return labs

    def _seed_insurance_providers(self):
        providers_data = [
            {
                "provider_id": _sha("insurance_sl_national"),
                "name": "Sierra Leone National Health Insurance",
                "license_number": "SL-INS-001",
                "public_key": _sha("pubkey_ins_001"),
            },
            {
                "provider_id": _sha("insurance_africahealth"),
                "name": "AfricaHealth Insurance",
                "license_number": "SL-INS-002",
                "public_key": _sha("pubkey_ins_002"),
            },
            {
                "provider_id": _sha("insurance_medicover"),
                "name": "MediCover Sierra Leone",
                "license_number": "SL-INS-003",
                "public_key": _sha("pubkey_ins_003"),
            },
        ]
        insurers = []
        for d in providers_data:
            obj, created = InsuranceProvider.objects.get_or_create(
                provider_id=d["provider_id"], defaults=d
            )
            insurers.append(obj)
            self._log("InsuranceProvider", obj.name, created)
        return insurers

    def _seed_patients(self, users):
        patient_users = [u for u in users if u.role == "PATIENT"]
        patients_data = [
            {
                "user": patient_users[0],
                "public_key": _sha(f"pubkey_{patient_users[0].username}"),
                "date_of_birth": date(1990, 5, 14),
                "blood_type": "O+",
                "allergies": "Penicillin",
                "emergency_contact": "Mohamed Sesay +23276123456",
            },
            {
                "user": patient_users[1],
                "public_key": _sha(f"pubkey_{patient_users[1].username}"),
                "date_of_birth": date(1985, 11, 22),
                "blood_type": "A-",
                "allergies": "None known",
                "emergency_contact": "Aminata Turay +23299654321",
            },
            {
                "user": patient_users[2],
                "public_key": _sha(f"pubkey_{patient_users[2].username}"),
                "date_of_birth": date(1975, 3, 8),
                "blood_type": "B+",
                "allergies": "Sulfa drugs",
                "emergency_contact": "Mary Conteh +23278987654",
            },
        ]
        patients = []
        for d in patients_data:
            obj = Patient.objects.filter(user=d["user"]).first()
            created = False
            if not obj:
                obj = Patient.objects.create(**d)
                created = True
            patients.append(obj)
            self._log("Patient", d["user"].get_full_name(), created)
        return patients

    def _seed_medical_records(self, patients, hospitals, txs):
        confirmed_txs = [t for t in txs if t.status == "CONFIRMED"]
        records_data = [
            {
                "patient": patients[0],
                "hospital": hospitals[0],
                "record_type": "DIAGNOSIS",
                "title": "Hypertension - Initial Diagnosis",
                "description": "Patient presents with stage-2 hypertension. BP: 160/100 mmHg. Started on Amlodipine 5mg.",
                "ipfs_hash": _sha("ipfs_diagnosis_001"),
                "file_size": 4096,
                "encryption_key_hash": _sha("enc_key_001"),
                "metadata_hash": _sha("meta_diagnosis_001"),
                "blockchain_tx": confirmed_txs[0] if confirmed_txs else None,
                "is_active": True,
            },
            {
                "patient": patients[0],
                "hospital": hospitals[0],
                "record_type": "LAB_RESULT",
                "title": "Full Blood Count - June 2025",
                "description": "Haemoglobin 12.4 g/dL, WBC 6.2 x10^9/L, Platelets 240 x10^9/L. Results within normal range.",
                "ipfs_hash": _sha("ipfs_lab_001"),
                "file_size": 2048,
                "encryption_key_hash": _sha("enc_key_002"),
                "metadata_hash": _sha("meta_lab_001"),
                "blockchain_tx": confirmed_txs[1] if len(confirmed_txs) > 1 else None,
                "is_active": True,
            },
            {
                "patient": patients[1],
                "hospital": hospitals[1],
                "record_type": "PRESCRIPTION",
                "title": "Metformin Prescription - Type 2 Diabetes",
                "description": "Metformin 500mg twice daily with meals. Follow up in 3 months. HbA1c target < 7%.",
                "ipfs_hash": _sha("ipfs_prescription_001"),
                "file_size": 1024,
                "encryption_key_hash": _sha("enc_key_003"),
                "metadata_hash": _sha("meta_prescription_001"),
                "blockchain_tx": confirmed_txs[2] if len(confirmed_txs) > 2 else None,
                "is_active": True,
            },
            {
                "patient": patients[1],
                "hospital": hospitals[0],
                "record_type": "IMAGING",
                "title": "Chest X-Ray - PA View",
                "description": "No active pulmonary disease. Cardiac silhouette within normal limits. Clear lung fields bilaterally.",
                "ipfs_hash": _sha("ipfs_imaging_001"),
                "file_size": 2097152,
                "encryption_key_hash": _sha("enc_key_004"),
                "metadata_hash": _sha("meta_imaging_001"),
                "blockchain_tx": None,
                "is_active": True,
            },
            {
                "patient": patients[2],
                "hospital": hospitals[2],
                "record_type": "SURGERY",
                "title": "Appendectomy - Laparoscopic",
                "description": "Uncomplicated laparoscopic appendectomy. Patient tolerated procedure well. Discharged day 2 post-op.",
                "ipfs_hash": _sha("ipfs_surgery_001"),
                "file_size": 8192,
                "encryption_key_hash": _sha("enc_key_005"),
                "metadata_hash": _sha("meta_surgery_001"),
                "blockchain_tx": None,
                "is_active": True,
            },
            {
                "patient": patients[2],
                "hospital": hospitals[1],
                "record_type": "DISCHARGE",
                "title": "Discharge Summary - Appendectomy",
                "description": "Patient discharged in stable condition. Wound care instructions given. Follow up GP in 7 days.",
                "ipfs_hash": _sha("ipfs_discharge_001"),
                "file_size": 3072,
                "encryption_key_hash": _sha("enc_key_006"),
                "metadata_hash": _sha("meta_discharge_001"),
                "blockchain_tx": None,
                "is_active": True,
            },
            {
                "patient": patients[0],
                "hospital": hospitals[0],
                "record_type": "INSURANCE",
                "title": "Insurance Pre-Auth - Hypertension Management",
                "description": "Pre-authorisation request for anti-hypertensive medication coverage. Approved by SL National Health Insurance.",
                "ipfs_hash": _sha("ipfs_insurance_001"),
                "file_size": 512,
                "encryption_key_hash": _sha("enc_key_007"),
                "metadata_hash": _sha("meta_insurance_001"),
                "blockchain_tx": None,
                "is_active": True,
            },
        ]
        records = []
        for d in records_data:
            obj = MedicalRecord.objects.filter(
                patient=d["patient"], title=d["title"]
            ).first()
            created = False
            if not obj:
                obj = MedicalRecord.objects.create(**d)
                created = True
            records.append(obj)
            self._log("MedicalRecord", obj.title[:40], created)
        return records

    def _seed_access_permissions(self, patients, records):
        perms_data = [
            {
                "record": records[0],
                "grantor": patients[0],
                "grantee": "National Reference Laboratory",
                "grantee_type": "LAB",
                "permission_type": "READ",
                "purpose": "Lab result correlation for hypertension management",
                "signature": _sha("sig_perm_001"),
                "zk_proof": json.dumps({"proof": _sha("zk_perm_001")}),
                "valid_until": timezone.now() + timedelta(days=180),
                "is_active": True,
            },
            {
                "record": records[2],
                "grantor": patients[1],
                "grantee": "AfricaHealth Insurance",
                "grantee_type": "INSURANCE",
                "permission_type": "READ",
                "purpose": "Insurance claim verification for diabetes medication",
                "signature": _sha("sig_perm_002"),
                "zk_proof": json.dumps({"proof": _sha("zk_perm_002")}),
                "valid_until": timezone.now() + timedelta(days=90),
                "is_active": True,
            },
            {
                "record": records[4],
                "grantor": patients[2],
                "grantee": "Freetown Medical Centre",
                "grantee_type": "HOSPITAL",
                "permission_type": "WRITE",
                "purpose": "Post-operative follow-up care continuity",
                "signature": _sha("sig_perm_003"),
                "zk_proof": json.dumps({"proof": _sha("zk_perm_003")}),
                "valid_until": timezone.now() + timedelta(days=30),
                "is_active": True,
            },
        ]
        for d in perms_data:
            obj = AccessPermission.objects.filter(
                record=d["record"], grantee=d["grantee"]
            ).first()
            created = False
            if not obj:
                d_copy = d.copy()
                d_copy["permission_id"] = _sha(f"perm_{d['grantee']}_{d['record'].record_id}")
                obj = AccessPermission.objects.create(**d_copy)
                created = True
            self._log("AccessPermission", f"{obj.grantee_type} -> {obj.permission_type}", created)

    def _seed_audit_logs(self, records):
        logs_data = [
            {
                "record": records[0],
                "actor": "dr_amara_koroma",
                "actor_type": "DOCTOR",
                "action": "CREATE",
                "details": {"note": "Initial record created during patient admission"},
                "ip_address": "192.168.1.10",
            },
            {
                "record": records[0],
                "actor": "dr_ibrahim_bangura",
                "actor_type": "DOCTOR",
                "action": "READ",
                "details": {"note": "Reviewed for hypertension treatment plan"},
                "ip_address": "192.168.1.11",
            },
            {
                "record": records[1],
                "actor": "dr_amara_koroma",
                "actor_type": "DOCTOR",
                "action": "CREATE",
                "details": {"note": "Lab results uploaded after FBC panel"},
                "ip_address": "192.168.1.10",
            },
            {
                "record": records[2],
                "actor": "dr_ibrahim_bangura",
                "actor_type": "DOCTOR",
                "action": "CREATE",
                "details": {"note": "Prescription issued for Type 2 Diabetes"},
                "ip_address": "192.168.1.12",
            },
            {
                "record": records[3],
                "actor": "dr_amara_koroma",
                "actor_type": "DOCTOR",
                "action": "SHARE",
                "details": {"shared_with": "AfricaHealth Insurance", "purpose": "pre-auth"},
                "ip_address": "192.168.1.10",
            },
            {
                "record": records[4],
                "actor": "dr_ibrahim_bangura",
                "actor_type": "DOCTOR",
                "action": "UPDATE",
                "details": {"note": "Post-operative notes added"},
                "ip_address": "192.168.1.12",
            },
            {
                "record": records[0],
                "actor": "unknown_agent",
                "actor_type": "HOSPITAL",
                "action": "ACCESS_DENIED",
                "details": {"reason": "Permission expired", "attempted_at": str(timezone.now())},
                "ip_address": "10.0.0.99",
            },
        ]
        for d in logs_data:
            log_id = _sha(
                f"log_{d['record'].record_id}_{d['actor']}_{d['action']}_{d['ip_address']}"
            )
            obj, created = AuditLog.objects.get_or_create(
                log_id=log_id,
                defaults=d,
            )
            self._log("AuditLog", f"{obj.action} by {obj.actor}", created)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _log(self, model, label, created):
        verb = self.style.SUCCESS("  created") if created else "  exists "
        self.stdout.write(f"{verb}  {model:<22} {label}")
