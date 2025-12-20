from cryptography.fernet import Fernet
import os
from loguru import logger as log
from dotenv import load_dotenv

load_dotenv()

def get_fernet():
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY not found in environment variables")
    key = key.strip('"').strip("'")
    return Fernet(key.encode())

def encrypt_data(data: str) -> str:
    """Encrypts a string using Fernet (AES)."""
    try:
        if not data:
            return data
        f = get_fernet()
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        log.error(f"Encryption failed: {e}")
        raise

def decrypt_data(data: str) -> str:
    """Decrypts a Fernet token back to string."""
    try:
        if not data:
            return data
        f = get_fernet()
        return f.decrypt(data.encode()).decode()
    except Exception as e:
        log.warning(f"Decryption failed (might be unencrypted data): {e}")
        return data
