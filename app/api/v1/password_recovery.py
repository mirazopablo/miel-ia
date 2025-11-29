from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.db import get_db_session
from app.infrastructure.repositories.user_repo import UserRepo
from app.core.security import create_password_reset_token, verify_password_reset_token, get_password_hash
from app.core.email_utils import send_reset_email

router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db_session)
):
    """
    Solicita un correo de recuperación de contraseña.
    Si el correo existe, envía un enlace con un token.
    """
    user_repo = UserRepo()
    user = user_repo.get_by_email(db, email=request.email)
    
    if user:
        # Generar token y enviar email solo si el usuario existe
        # (Para seguridad, no revelamos si el usuario existe o no al cliente,
        # pero internamente sí procesamos el envío)
        token = create_password_reset_token(user.email)
        send_reset_email(user.email, token)
    
    # Siempre retornamos éxito para evitar enumeración de usuarios
    return {"message": "Si el correo existe, se ha enviado un enlace de recuperación."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db_session)
):
    """
    Restablece la contraseña usando un token válido.
    """
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )
    
    user_repo = UserRepo()
    user = user_repo.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Actualizar contraseña
    new_hash = get_password_hash(request.new_password)
    user.password = new_hash
    db.add(user)
    db.commit()
    
    return {"message": "Contraseña actualizada exitosamente"}
