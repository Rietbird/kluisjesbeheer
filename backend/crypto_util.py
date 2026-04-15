"""Encrypt/decrypt sensitive settings using Fernet (AES-128-CBC + HMAC)."""
import base64
import hashlib
from cryptography.fernet import Fernet
from config import config


def _get_fernet():
    """Derive a Fernet key from the app's SecretKey."""
    secret = config.get('SecretKey', '').encode('utf-8')
    # Fernet needs a 32-byte url-safe base64-encoded key; derive from SecretKey via SHA-256
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt(plaintext):
    """Encrypt a string, return base64 token."""
    if not plaintext:
        return ''
    return _get_fernet().encrypt(plaintext.encode('utf-8')).decode('ascii')


def decrypt(token):
    """Decrypt a Fernet token back to string."""
    if not token:
        return ''
    return _get_fernet().decrypt(token.encode('ascii')).decode('utf-8')
