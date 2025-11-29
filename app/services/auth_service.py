# app/services/auth_service.py
from datetime import timedelta
from typing import List
from jose import JWTError
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.api.v1.register import get_user_role_service, get_user_service

from ..infrastructure.db.DTOs.user_role_dto import UserRoleResponseDTO

from ..services.user_role_service import UserRoleService
from ..services.user_service import UserService
from ..core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from ..core.config import settings
from ..infrastructure.repositories.user_repo import UserRepo
from ..infrastructure.db.DTOs.auth_schema import Token, UserLogin, UserOut
from ..core.db import get_db_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class AuthService:
    def __init__(self, user_repo: UserRepo, user_service: UserService, user_role_service: UserRoleService):
        self.__user_repo = user_repo
        self.__user_service = user_service
        self.__user_role_service = user_role_service

    def login(self, db: Session, user_login: UserLogin) -> Token:
        user = self.__user_repo.authenticate(db, email=user_login.email, password=user_login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password (AuthService)",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_dto = self.__user_service.find_by_email(db, user_login.email)
        
        user_roles: List[UserRoleResponseDTO] = self.__user_role_service.get_user_roles_by_user_id(db, user_dto.id)
        
        token_data = {
            "sub": user.email,
            "user_id": str(user_dto.id), 
            "roles": [str(role.role_id) for role in user_roles]
        }

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token, token_type="bearer")

    def get_current_user(self, db: Session, token: str = Depends(oauth2_scheme)) -> UserOut:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = decode_access_token(token)
            if payload is None:
                raise credentials_exception
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user = self.__user_repo.get_by_email(db, email=email)
        if user is None:
            raise credentials_exception
        return user
    

def get_auth_service(
    db: Session = Depends(get_db_session),
    user_service: UserService = Depends(get_user_service),
    user_role_service: UserRoleService = Depends(get_user_role_service)
) -> AuthService:
    user_repo = UserRepo(db)
    return AuthService(user_repo, user_service, user_role_service)