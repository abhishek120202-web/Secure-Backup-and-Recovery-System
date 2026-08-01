"""
Encryption services module.

This module provides encryption and decryption functionality.
"""

import base64
import hashlib
import os
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """
    Service class for encryption operations.

    Provides AES-256 encryption, decryption, and hash generation.
    """

    def __init__(self):
        """Initialize EncryptionService."""
        pass

    def encrypt_aes256(self, plaintext: bytes, key: bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM.

        Args:
            plaintext: Data to encrypt
            key: Encryption key (256-bit)

        Returns:
            Encrypted payload with nonce prepended
        """
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    def decrypt_aes256(self, ciphertext: bytes, key: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM.

        Args:
            ciphertext: Encrypted payload with nonce prepended
            key: Decryption key (256-bit)

        Returns:
            Decrypted plaintext
        """
        nonce = ciphertext[:12]
        encrypted_data = ciphertext[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, encrypted_data, None)

    def generate_sha256_hash(self, data: bytes) -> str:
        """
        Generate SHA-256 hash of data.

        Args:
            data: Data to hash

        Returns:
            Hex string representation of SHA-256 hash
        """
        return hashlib.sha256(data).hexdigest()

    def derive_key_from_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: User password
            salt: Salt for key derivation (generated if not provided)

        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=200_000,
        )
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
