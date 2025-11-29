import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..infrastructure.repositories.user_role_repo import UserRoleRepo
from ..infrastructure.repositories.user_repo import UserRepo
from ..infrastructure.repositories.role_repo import RoleRepo
from typing import List, Union
from ..infrastructure.db.DTOs.user_role_dto import (
    UserRoleCreateDTO,
    UserRoleUpdateDTO,
    UserRoleResponseDTO,
)

class UserRoleService:
    def __init__(
        self,
        user_role_repo: UserRoleRepo,
        user_repo: UserRepo,
        role_repo: RoleRepo
    ):
        self.__user_role_repo = user_role_repo
        self.__user_repo = user_repo
        self.__role_repo = role_repo
    
    def _normalize_id(self, id_value: Union[str, uuid.UUID]) -> str:
        """Normaliza IDs a string para consistencia"""
        if isinstance(id_value, uuid.UUID):
            return str(id_value)
        return str(id_value) if id_value is not None else None
    
    def get_user_role(self, db: Session, id: Union[str, uuid.UUID]) -> UserRoleResponseDTO:
        """Obtiene una relación user_role por UUID"""
        normalized_id = self._normalize_id(id)
        user_role = self.__user_role_repo.get(db, normalized_id)
        if not user_role:
            raise HTTPException(status_code=404, detail="UserRole not found (UserRoleService)")
        return UserRoleResponseDTO.model_validate(user_role)
    
    def get_users_by_role_id(self, db: Session, role_id: Union[str, uuid.UUID]) -> List:
        """
        Obtiene todos los usuarios que tienen un rol específico.
        Retorna objetos User completos, no UserRole.
        """
        normalized_role_id = self._normalize_id(role_id)
        
        user_roles = self.__user_role_repo.get_by_role_id(db, normalized_role_id)
        
        user_ids = [ur.user_id for ur in user_roles]
        
        if not user_ids:
            return []
        
        users = []
        for user_id in user_ids:
            user = self.__user_repo.get(db, id=user_id)
            if user:
                users.append(user)
        
        return users
    
    def get_user_roles_by_user_id(self, db: Session, user_id: Union[str, uuid.UUID]) -> List[UserRoleResponseDTO]:
        """
        Obtiene todos los UserRoleResponseDTO para un user_id dado.
        """
        normalized_user_id = self._normalize_id(user_id)
        user_roles_orm = self.__user_role_repo.get_by_user_id(db, normalized_user_id)
        return [UserRoleResponseDTO.model_validate(ur) for ur in user_roles_orm]

    def create_user_role(self, db: Session, obj_in: UserRoleCreateDTO) -> UserRoleResponseDTO:
        user_id = self._normalize_id(obj_in.user_id)
        role_id = self._normalize_id(obj_in.role_id)

        
        user = self.__user_repo.get(db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found (UserRoleService)")
        
        role = self.__role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found (UserRoleService)")

        existing = self.__user_role_repo.get_by_user_and_role(db, user_id, role_id)
        if existing:
            raise HTTPException(status_code=400, detail="User already has this role assigned (UserRoleService)")
        
        normalized_obj_in = UserRoleCreateDTO(
            user_id=user_id,
            role_id=role_id
        )
        
        user_role = self.__user_role_repo.create(db, obj_in=normalized_obj_in)
        return UserRoleResponseDTO.model_validate(user_role)

    def update_user_role(self, db: Session, id: Union[str, uuid.UUID], obj_in: UserRoleUpdateDTO) -> UserRoleResponseDTO:
        normalized_id = self._normalize_id(id)
        db_user_role = self.__user_role_repo.get(db, normalized_id)
        if not db_user_role:
            raise HTTPException(status_code=404, detail="UserRole not found (UserRoleService)")

        if obj_in.user_id:
            normalized_user_id = self._normalize_id(obj_in.user_id)
            if not self.__user_repo.get(db, normalized_user_id):
                raise HTTPException(status_code=404, detail="User not found (UserRoleService)")
        
        if obj_in.role_id:
            normalized_role_id = self._normalize_id(obj_in.role_id)
            if not self.__role_repo.get_by_id(normalized_role_id):
                raise HTTPException(status_code=404, detail="Role not found (UserRoleService)")
            
        updated = self.__user_role_repo.update(db, db_obj=db_user_role, obj_in=obj_in)
        return UserRoleResponseDTO.model_validate(updated)

    def delete_user_role(self, db: Session, id: Union[str, uuid.UUID]) -> UserRoleResponseDTO:
        normalized_id = self._normalize_id(id)
        db_user_role = self.__user_role_repo.get(db, normalized_id)
        if not db_user_role:
            raise HTTPException(status_code=404, detail="UserRole not found (UserRoleService)")
        deleted = self.__user_role_repo.delete(db, id=normalized_id)
        return UserRoleResponseDTO.model_validate(deleted)