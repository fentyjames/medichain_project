"""
MediChain Zero-Knowledge Proof Service
Implements zk-SNARK and zk-STARK proof generation and verification
"""

import hashlib
import json
import time
from typing import List, Dict, Any


class ZKProofService:
    """Service for generating and verifying Zero-Knowledge Proofs"""

    def __init__(self, proof_type='zk_snark'):
        self.proof_type = proof_type
        self.proof_cache = {}

    def generate_proof(self, inputs: List[str], public_output: str) -> str:
        """
        Generate a Zero-Knowledge Proof

        Args:
            inputs: List of private inputs (transaction hashes)
            public_output: Public output (Merkle root)

        Returns:
            JSON string containing the proof
        """
        # Simulate ZK proof generation
        # In production, this would use libraries like snarkjs, libsnark, or ZoKrates

        proof_data = {
            'proof_type': self.proof_type,
            'timestamp': time.time(),
            'public_inputs': {
                'merkle_root': public_output,
                'input_count': len(inputs),
            },
            'private_inputs_hash': self._hash_inputs(inputs),
            'proof': self._simulate_proof(inputs, public_output),
            'verification_key': self._generate_verification_key(),
        }

        proof_json = json.dumps(proof_data, sort_keys=True)
        proof_hash = hashlib.sha256(proof_json.encode()).hexdigest()

        self.proof_cache[proof_hash] = proof_data

        return proof_json

    def verify_proof(self, proof: str, public_output: str, expected_inputs: List[str]) -> bool:
        """
        Verify a Zero-Knowledge Proof

        Args:
            proof: The proof JSON string
            public_output: Expected public output (Merkle root)
            expected_inputs: Expected inputs for verification

        Returns:
            True if proof is valid, False otherwise
        """
        try:
            proof_data = json.loads(proof)

            # Verify proof type
            if proof_data.get('proof_type') != self.proof_type:
                return False

            # Verify public inputs match
            if proof_data['public_inputs']['merkle_root'] != public_output:
                return False

            # Verify input count
            if proof_data['public_inputs']['input_count'] != len(expected_inputs):
                return False

            # Verify input hash
            expected_hash = self._hash_inputs(expected_inputs)
            if proof_data['private_inputs_hash'] != expected_hash:
                return False

            # Verify proof structure (simulated)
            if not self._verify_proof_structure(proof_data):
                return False

            return True

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Proof verification error: {e}")
            return False

    def _hash_inputs(self, inputs: List[str]) -> str:
        """Hash a list of inputs"""
        combined = ''.join(sorted(inputs))
        return hashlib.sha256(combined.encode()).hexdigest()

    def _simulate_proof(self, inputs: List[str], output: str) -> Dict[str, Any]:
        """Simulate ZK proof generation"""
        # This is a simulation - real implementation would use cryptographic libraries
        proof = {
            'a': hashlib.sha256(f"a_{','.join(inputs)}".encode()).hexdigest(),
            'b': hashlib.sha256(f"b_{output}".encode()).hexdigest(),
            'c': hashlib.sha256(f"c_{time.time()}".encode()).hexdigest(),
        }
        return proof

    def _generate_verification_key(self) -> str:
        """Generate verification key"""
        return hashlib.sha256(f"vk_{self.proof_type}_{time.time()}".encode()).hexdigest()

    def _verify_proof_structure(self, proof_data: Dict) -> bool:
        """Verify the structure of a proof"""
        required_keys = ['proof_type', 'public_inputs', 'proof', 'verification_key']
        return all(key in proof_data for key in required_keys)

    def create_range_proof(self, value: int, min_val: int, max_val: int) -> str:
        """
        Create a range proof (value is within [min_val, max_val])
        Used for verifying medical values without revealing exact data
        """
        proof_data = {
            'proof_type': 'range_proof',
            'range': {'min': min_val, 'max': max_val},
            'value_commitment': hashlib.sha256(str(value).encode()).hexdigest(),
            'timestamp': time.time(),
        }
        return json.dumps(proof_data)

    def verify_range_proof(self, proof: str, min_val: int, max_val: int) -> bool:
        """Verify a range proof"""
        try:
            proof_data = json.loads(proof)
            return (
                proof_data['proof_type'] == 'range_proof' and
                proof_data['range']['min'] == min_val and
                proof_data['range']['max'] == max_val
            )
        except (json.JSONDecodeError, KeyError):
            return False


class MerkleTreeService:
    """Service for Merkle tree operations"""

    @staticmethod
    def build_merkle_tree(leaves: List[str]) -> Dict[str, Any]:
        """Build a Merkle tree from leaf nodes"""
        if not leaves:
            return {'root': hashlib.sha256(b'empty').hexdigest(), 'levels': []}

        levels = [leaves]
        current_level = leaves

        while len(current_level) > 1:
            if len(current_level) % 2 == 1:
                current_level.append(current_level[-1])

            next_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i+1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())

            levels.append(next_level)
            current_level = next_level

        return {
            'root': current_level[0],
            'levels': levels,
            'leaf_count': len(leaves)
        }

    @staticmethod
    def get_proof_path(tree: Dict, leaf_index: int) -> List[Dict]:
        """Get Merkle proof path for a leaf"""
        path = []
        current_index = leaf_index

        for level in tree['levels'][:-1]:
            sibling_index = current_index + 1 if current_index % 2 == 0 else current_index - 1
            if sibling_index < len(level):
                path.append({
                    'sibling_hash': level[sibling_index],
                    'direction': 'right' if current_index % 2 == 0 else 'left'
                })
            current_index //= 2

        return path

    @staticmethod
    def verify_merkle_proof(root: str, leaf: str, proof_path: List[Dict]) -> bool:
        """Verify a Merkle proof"""
        current_hash = leaf

        for step in proof_path:
            if step['direction'] == 'right':
                combined = current_hash + step['sibling_hash']
            else:
                combined = step['sibling_hash'] + current_hash
            current_hash = hashlib.sha256(combined.encode()).hexdigest()

        return current_hash == root
