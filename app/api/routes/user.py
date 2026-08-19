# app/api/routes/user.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ...api.v1.auth import get_current_user
from ...infrastructure.db.DTOs.auth_schema import UserOut
from ...core.db import get_db_session as get_db
from ...infrastructure.db.DTOs.user_dto import (
    UserCreateDTO,
    UserUpdateDTO,
    UserResponseDTO as UserResponse,
    UserCreateInternal
)
from ...infrastructure.db.DTOs.user_role_dto import UserRoleCreateDTO
from ...infrastructure.repositories.user_repo import UserRepo
from ...infrastructure.repositories.user_role_repo import UserRoleRepo
from ...infrastructure.repositories.role_repo import RoleRepo
from ...services.user_service import UserService
from ...services.user_role_service import UserRoleService

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"]
)

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_repo = UserRepo(db)
    return UserService(user_repo=user_repo)

def get_user_repository(db: Session = Depends(get_db)) -> UserRepo:
    return UserRepo(db)

def get_user_role_service(db: Session = Depends(get_db)) -> UserRoleService:
    user_role_repo = UserRoleRepo(db)
    user_repo = UserRepo(db)
    role_repo = RoleRepo(db)
    return UserRoleService(
        user_role_repo=user_role_repo,
        user_repo=user_repo,
        role_repo=role_repo
    )

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateDTO,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    user_role_service: UserRoleService = Depends(get_user_role_service),
    current_user: UserOut = Depends(get_current_user)
) -> UserResponse:
    """Crear un nuevo usuario"""
    try:
        user_for_creation = UserCreateInternal(
            name=user_data.name,
            last_name=user_data.last_name or "",
            email=user_data.email,
            dni=user_data.dni,
            password=user_data.password
        )
        
        user = user_service.create_user(db, user_for_creation)        
        role_id = user_data.role_id
        
        try:
            user_role_data = UserRoleCreateDTO(
                user_id=user.id,
                role_id=role_id
            )
            user_role_service.create_user_role(db, user_role_data)
        except Exception as role_error:
            user_service.delete(db, user.id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error assigning role to user: {str(role_error)}"
            )
        
        updated_user = user_service.find_by_id(db, user.id)
        return UserResponse.model_validate(updated_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating user: {str(e)}"
        )

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_repo: UserRepo = Depends(get_user_repository),
    current_user: UserOut = Depends(get_current_user)
) -> List[UserResponse]:
    """Obtener lista de usuarios"""
    try:
        users = user_repo.get_all(db, skip=skip, limit=limit)
        return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users: {str(e)}"
        )

@router.get("/by-role/{role_id}", response_model=List[UserResponse])
async def get_users_by_role(
    role_id: uuid.UUID,  
    db: Session = Depends(get_db),
    user_repo: UserRepo = Depends(get_user_repository),
    current_user: UserOut = Depends(get_current_user)
) -> List[UserResponse]:
    """Obtener usuarios por rol"""
    try:
        users = user_repo.get_users_by_role_id(db, role_id)
        return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving users by role: {str(e)}"
        )

@router.get("/by-id/{user_id}", response_model=UserOut)
def get_user_by_uuid(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: UserOut = Depends(get_current_user)
) -> UserOut:
    """Obtiene un usuario por su UUID"""
    user = user_service.find_by_id(db, user_id=user_id)
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    user_data: UserUpdateDTO,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: UserOut = Depends(get_current_user)
) -> UserResponse:
    """Actualizar un usuario"""
    try:
        updated_user = user_service.update(db, user_id=user_id, user_update=user_data)
        return UserResponse.model_validate(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user: {str(e)}"
        )


@router.delete("/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    user_role_service: UserRoleService = Depends(get_user_role_service),
    current_user: UserOut = Depends(get_current_user)
) -> UserResponse:
    """Eliminar un usuario"""
    try:
        user_roles = user_role_service.get_user_roles_by_user_id(db, user_id)
        
        for user_role in user_roles:
            user_role_service.delete_user_role(db, user_role.id)
        
        deleted_user = user_service.delete(db, user_id=user_id)
        return UserResponse.model_validate(deleted_user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting user: {str(e)}"
        )
    
@router.get("/by-email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: UserOut = Depends(get_current_user)
) -> UserResponse:
    """Obtener un usuario por email"""
    try:
        user = user_service.find_by_email(db, email=email)
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )

@router.get("/by-dni/{dni}", response_model=UserResponse)
async def get_user_by_dni(
    dni: str,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    current_user: UserOut = Depends(get_current_user)
) -> UserResponse:
    """Obtener un usuario por DNI"""
    try:
        user = user_service.find_by_dni(db, dni=dni)
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )