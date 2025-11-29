# services/role_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Union
import uuid
from ..infrastructure.repositories.role_repo import RoleRepo
from ..infrastructure.db.models.role import Role
from ..infrastructure.db.DTOs.role_dto import RoleBaseDTO as RoleDTO, RoleResponseDTO

class RoleService:
    def __init__(self, role_repo: RoleRepo):
        self._role_repo = role_repo

    def get_role(self, role_id: Union[str, uuid.UUID]) -> Role:
        """Obtiene el rol completo por su ID (acepta string o UUID)"""
        role = self._role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found (RoleService)"
            )
        return role

    def get_role_name(self, role_id: Union[str, uuid.UUID]) -> str:
        """Obtiene solo el nombre del rol (acepta string o UUID)"""
        name = self._role_repo.get_role_name(role_id)
        if not name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {role_id} not found (RoleService)"
            )
        return name

    def get_all_roles(self) -> List[RoleResponseDTO]:
        """Obtiene todos los roles"""
        roles = self._role_repo.get_all()
        return [RoleResponseDTO.model_validate(role) for role in roles]
    
    def create_role(self, name: str) -> RoleDTO:
        """Crea un nuevo rol"""
        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is required (RoleService)"
            )
        role = self._role_repo.create(name=name)
        log.success(f"Role created successfully (RoleService)")
        return RoleDTO.model_validate(role)