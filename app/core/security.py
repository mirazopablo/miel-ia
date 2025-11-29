from click import DateTime
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv
from loguru import logger as log
from .config import settings

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "secret-key-para-desarrollo")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
    deprecated="auto"
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su versión hasheada"""
    try:      
        if not hashed_password.startswith('$argon2'):
            raise ValueError("Unknown hash format, expected Argon2 hash.")
            return False
        result = pwd_context.verify(plain_password, hashed_password)
        log.info(f"Verification result: {result}")
        if not result:
            try:
                new_hash = pwd_context.hash(plain_password)                
                stored_params = hashed_password.split('$')[3] if len(hashed_password.split('$')) > 3 else "unknown"
                new_params = new_hash.split('$')[3] if len(new_hash.split('$')) > 3 else "unknown"                
                if stored_params != new_params:
                    log.warning("Hash parameters differ, consider rehashing the password.")

            except Exception as debug_e:
                log.error(f"Error during rehashing attempt: {debug_e}")
        return result
        
    except Exception as e:
        log.error(f"Error in verify_password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """Genera un hash seguro de la contraseña"""
    try:
        hash_result = pwd_context.hash(password)
        return hash_result
    except Exception as e:
        log.error(f"Error generating hash: {e}")
        raise

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT de acceso"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """Decodifica y verifica un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def create_password_reset_token(email: str) -> str:
    """Crea un token específico para recuperación de contraseña"""
    expire = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "type": "password_reset", "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verifica el token de recuperación y devuelve el email si es válido.
    Retorna None si es inválido o expiró.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None

def emergency_password_reset(email: str, new_password: str):
    """
    Función de emergencia para resetear contraseña en desarrollo
    """
    try:
        from app.core.db import engine
        from sqlalchemy import text
        
        new_hash = get_password_hash(new_password)
        
        with engine.connect() as conn:
            result = conn.execute(
                text("UPDATE users SET password = :new_hash WHERE email = :email"),
                {"new_hash": new_hash, "email": email}
            )
            conn.commit()

        return True
        
    except Exception as e:
        log.error(f"Error resetting password: {e}")
        return False