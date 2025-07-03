from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as rsa_padding
import os
import base64
from typing import Tuple, Optional

class RSA:
    def __init__(self) -> None:
        """Generate RSA key pair using cryptography library"""
        print("Generating RSA key pair...")

        # Generate private key (2048 bits for real security)
        self.private_key: RSAPrivateKey = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Get the public key
        self.public_key: RSAPublicKey = self.private_key.public_key()

        print("✓ RSA keys generated successfully!")
        print(f"✓ Key size: 2048 bits")
        print(f"✓ Public exponent: 65537")

    def get_public_key_bytes(self) -> bytes:
        """Serialize public key for transmission

        Returns:
            bytes: Public key in PEM format as bytes
        """
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def encrypt_message(self, message: bytes, public_key: RSAPublicKey) -> bytes:
        """Encrypt message using public key

        Args:
            message (str): Plain text message to encrypt
            public_key (RSAPublicKey): RSA public key object

        Returns:
            bytes: Encrypted message bytes
        """


        ciphertext: bytes = public_key.encrypt(
            message,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def decrypt_message(self, ciphertext: bytes) -> str:
        """Decrypt message using private key

        Args:
            ciphertext (bytes): Encrypted message bytes

        Returns:
            str: Decrypted plain text message
        """


        plaintext: bytes = self.private_key.decrypt(
            ciphertext,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('utf-8')

    def load_public_key_from_bytes(self, public_key_bytes: bytes) -> RSAPublicKey:
        """Load public key from bytes (simulates receiving over network)

        Args:
            public_key_bytes (bytes): Public key in PEM format as bytes

        Returns:
            RSAPublicKey: Loaded RSA public key object
        """
        return serialization.load_pem_public_key(public_key_bytes)

    def encrypt_aes_key(self, aes_key: bytes, public_key: RSAPublicKey) -> bytes:
        """Encrypt AES key using RSA public key

        Args:
            aes_key (bytes): 32-byte AES key to encrypt
            public_key (RSAPublicKey): RSA public key object

        Returns:
            bytes: Encrypted AES key bytes
        """

        encrypted_aes_key: bytes = public_key.encrypt(
            aes_key,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_aes_key

    def decrypt_aes_key(self, encrypted_aes_key: bytes) -> bytes:
        """Decrypt AES key using RSA private key

        Args:
            encrypted_aes_key (bytes): Encrypted AES key bytes

        Returns:
            bytes: Decrypted 32-byte AES key
        """

        aes_key: bytes = self.private_key.decrypt(
            encrypted_aes_key,
            rsa_padding.OAEP(
                mgf=rsa_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return aes_key