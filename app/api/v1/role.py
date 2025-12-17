from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...infrastructure.db.DTOs.auth_schema import UserOut

from ...api.v1.auth import get_current_user
from ...services.role_service import RoleService
from ...infrastructure.repositories.role_repo import RoleRepo
from ...infrastructure.db.DTOs.role_dto import RoleBaseDTO, RoleResponseDTO
from core.db import get_db_session as get_db

router = APIRouter(prefix="/temp-roles", tags=["Temporary Role Creation"])
def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    role_repo = RoleRepo(db)  
    role_repo.db = db
    return RoleService(role_repo)


@router.post(
    "/create",
    response_model=RoleBaseDTO,
    status_code=status.HTTP_201_CREATED,
    description="TEMPORARY ENDPOINT - Only for initial role creation",
    include_in_schema=True
)
async def create_temp_role(
    role_data: RoleBaseDTO,
    role_service: RoleService = Depends(get_role_service),
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    """
    TEMPORARY ENDPOINT - Creates a new role with UUID.
    """
    try:

        return role_service.create_role(role_data.name)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating role: {str(e)}"
        )
@router.get("/", response_model=List[RoleResponseDTO])
async def get_all_roles(
    role_service: RoleService = Depends(get_role_service),
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)

):
    """
    Obtiene todos los roles registrados en el sistema con sus UUIDs.
    Útil para obtener los IDs de roles como 'admin', 'doctor', etc.
    """
    return role_service.get_all_roles()

@router.get("/{role_id}", response_model=str)
async def get_role_name_by_id(
    role_id: UUID,
    role_service: RoleService = Depends(get_role_service),
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user)
):
    """
    Obtiene SOLO el nombre de un rol específico por su UUID.
    """
    return role_service.get_role(role_id)