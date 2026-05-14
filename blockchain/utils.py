"""
MediChain Encryption Utilities
AES-256-GCM encryption for off-chain medical data storage
"""

import base64
import hashlib
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """Service for encrypting and decrypting medical data"""

    def __init__(self):
        self.algorithm = 'AES-256-GCM'

    def derive_key(self, password: str, salt: bytes = None) -> tuple:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        return key, salt

    def encrypt(self, data: bytes, password: str) -> dict:
        """
        Encrypt data using AES-256-GCM

        Returns:
            dict with ciphertext, nonce, salt, and tag
        """
        key, salt = self.derive_key(password)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, data, None)

        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'nonce': base64.b64encode(nonce).decode(),
            'salt': base64.b64encode(salt).decode(),
            'algorithm': self.algorithm,
        }

    def decrypt(self, encrypted_data: dict, password: str) -> bytes:
        """Decrypt data encrypted with AES-256-GCM"""
        salt = base64.b64decode(encrypted_data['salt'])
        key, _ = self.derive_key(password, salt)

        aesgcm = AESGCM(key)
        nonce = base64.b64decode(encrypted_data['nonce'])
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])

        return aesgcm.decrypt(nonce, ciphertext, None)

    def hash_data(self, data: bytes) -> str:
        """Compute SHA-256 hash of data"""
        return hashlib.sha256(data).hexdigest()

    def generate_keypair(self) -> dict:
        """Generate ECC keypair for signing"""
        from cryptography.hazmat.primitives.asymmetric import ec
        private_key = ec.generate_private_key(ec.SECP256R1())
        public_key = private_key.public_key()

        from cryptography.hazmat.primitives import serialization
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return {
            'private_key': private_pem.decode(),
            'public_key': public_pem.decode(),
        }

    def sign_data(self, data: bytes, private_key_pem: str) -> str:
        """Sign data with private key"""
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None
        )
        signature = private_key.sign(data, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(signature).decode()

    def verify_signature(self, data: bytes, signature: str, public_key_pem: str) -> bool:
        """Verify signature with public key"""
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        try:
            public_key.verify(
                base64.b64decode(signature),
                data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except Exception:
            return False


class IPFSService:
    """Service for IPFS interactions"""

    def __init__(self, gateway='https://ipfs.io/ipfs/'):
        self.gateway = gateway
        self.local_api = 'http://localhost:5001/api/v0'

    def add_file(self, file_data: bytes) -> str:
        """Add file to IPFS and return CID"""
        try:
            import ipfshttpclient
            client = ipfshttpclient.connect(self.local_api)
            result = client.add_bytes(file_data)
            return result
        except Exception:
            # Fallback: compute hash as simulated CID
            return f"Qm{hashlib.sha256(file_data).hexdigest()[:44]}"

    def get_file(self, cid: str) -> bytes:
        """Retrieve file from IPFS by CID"""
        try:
            import ipfshttpclient
            client = ipfshttpclient.connect(self.local_api)
            return client.cat(cid)
        except Exception:
            return b''

    def get_gateway_url(self, cid: str) -> str:
        """Get HTTP gateway URL for CID"""
        return f"{self.gateway}{cid}"
