from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives import serialization
import os
import base64
from typing import Tuple, Optional


class AES:
    def __init__(self, key: bytes = None) -> None:
        if key is not None and len(key) != 32:
            raise ValueError("AES key must be 32 bytes (256 bits) long")
        if key is not None:
            self.key: bytes = key
        else:
            self.key: bytes = self.generate_key()

    def generate_key(self) -> bytes:
        """Generate a random 256-bit AES key

        Returns:
            bytes: 32-byte AES key (256 bits)
        """
        return os.urandom(32)  # 32 bytes = 256 bits

    def generate_key_from_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Generate AES key from password using PBKDF2

        Args:
            password (str): Password string to derive key from
            salt (Optional[bytes]): Optional salt bytes. If None, generates random 16-byte salt

        Returns:
            Tuple[bytes, bytes]: (32-byte AES key, 16-byte salt)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256-bit key
            salt=salt,
            iterations=100000,  # Industry standard
        )
        key: bytes = kdf.derive(password.encode())
        return key, salt

    def encrypt_message(self, message: str) -> bytes:
        """Encrypt message using AES-256 in CBC mode

        Args:
            message (str): Plain text message to encrypt
            key (bytes): 32-byte AES key

        Returns:
            bytes: IV + encrypted data (IV is first 16 bytes)
        """
        # Generate random IV (Initialization Vector)
        iv: bytes = os.urandom(16)  # 16 bytes for AES block size

        # Pad the message to block size
        padder = padding.PKCS7(128).padder()  # 128 bits = 16 bytes
        padded_data: bytes = padder.update(message.encode()) + padder.finalize()

        # Create cipher and encrypt
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        ciphertext: bytes = encryptor.update(padded_data) + encryptor.finalize()

        # Return IV + ciphertext (IV is not secret, just needs to be unique)
        return iv + ciphertext

    def decrypt_message(self, encrypted_data: bytes) -> str:
        """Decrypt message using AES-256

        Args:
            encrypted_data (bytes): IV + ciphertext (IV is first 16 bytes)
            key (bytes): 32-byte AES key

        Returns:
            str: Decrypted plain text message
        """
        # Extract IV and ciphertext
        iv: bytes = encrypted_data[:16]
        ciphertext: bytes = encrypted_data[16:]

        # Create cipher and decrypt
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_plaintext: bytes = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        plaintext: bytes = unpadder.update(padded_plaintext) + unpadder.finalize()

        return plaintext.decode()