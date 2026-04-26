"""Cryptographic utilities for encrypting and decrypting .env file contents."""

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet


SALT_SIZE = 16
ITERATIONS = 390000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    raw_key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(raw_key)


def encrypt(plaintext: str, password: str) -> bytes:
    """Encrypt plaintext using a password-derived key.

    Returns salt + encrypted data as bytes.
    """
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    token = Fernet(key).encrypt(plaintext.encode())
    return salt + token


def decrypt(ciphertext: bytes, password: str) -> str:
    """Decrypt ciphertext using a password-derived key.

    Expects salt prepended to the encrypted token.
    """
    salt = ciphertext[:SALT_SIZE]
    token = ciphertext[SALT_SIZE:]
    key = derive_key(password, salt)
    return Fernet(key).decrypt(token).decode()
