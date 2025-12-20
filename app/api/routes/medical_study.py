from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union
from enum import Enum
from loguru import logger as log

from ...infrastructure.db.DTOs.auth_schema import UserOut

from ...services.medical_study_service import MedicalStudyService
from ...infrastructure.repositories.medical_study_repo import MedicalStudyRepo
from ...infrastructure.db.DTOs.medical_study_dto import MedicalStudyUpdateDTO
from ...infrastructure.repositories.user_repo import UserRepo
from ...infrastructure.db.DTOs.response import MessageResponse
from ...infrastructure.db.DTOs.medical_study_dto import MedicalStudyCreateDTO, MedicalStudyResponseDTO
from ...core.db import get_db_session as get_db
from ...services.auth_service import get_auth_service
from ...api.v1.auth import get_current_user


class MedicalStudySearchType(str, Enum):
    ALL = "all"
    ID = "id"
    PATIENT_DNI = "patient_dni"
    PATIENT_NAME = "patient_name"

router = APIRouter(prefix="/medical_studies", tags=["Medical Studies"])

def get_medical_study_service(db: Session = Depends(get_db)) -> MedicalStudyService:
    study_repo = MedicalStudyRepo()
    user_repo = UserRepo(db)
    return MedicalStudyService(medical_study_repo=study_repo, user_repo=user_repo)


@router.post("/", response_model=MedicalStudyResponseDTO, status_code=status.HTTP_201_CREATED)
def create_medical_study(
    study_data: MedicalStudyCreateDTO,
    db: Session = Depends(get_db),
    study_service: MedicalStudyService = Depends(get_medical_study_service),
    current_user: UserOut = Depends(get_current_user)
) -> MedicalStudyResponseDTO:
    """
    Crea una nueva orden de estudio médico.
    """
    try:
        return study_service.create_study(db, study_data=study_data)
    except Exception as e:
        log.error(f"Error al crear el estudio: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el estudio")

@router.get("/search/", response_model=Union[List[MedicalStudyResponseDTO], MedicalStudyResponseDTO])
def search_medical_studies(
    search_type: MedicalStudySearchType = Query(..., description="Tipo de búsqueda a realizar"),
    study_id: Optional[str] = Query(None, description="ID del estudio (si search_type es 'id')"),
    patient_dni: Optional[str] = Query(None, description="DNI del paciente (si search_type es 'patient_dni')"),
    access_code: Optional[str] = Query(None, description="Código de acceso del paciente (si search_type es 'patient_dni')"),
    patient_name: Optional[str] = Query(None, description="Nombre o apellido del paciente (si search_type es 'patient_name')"),
    db: Session = Depends(get_db),
    study_service: MedicalStudyService = Depends(get_medical_study_service),
    current_user: UserOut = Depends(get_current_user)
) -> Union[List[MedicalStudyResponseDTO], MedicalStudyResponseDTO]:
    """
    Búsqueda unificada de estudios médicos.
    """
    if search_type == MedicalStudySearchType.ALL:
        return study_service.get_all_studies(db)
    
    if search_type == MedicalStudySearchType.ID:
        if not study_id:
            raise HTTPException(status_code=400, detail="study_id is required for 'id' search type")
        return study_service.get_by_id(db, study_id=study_id)
        
    if search_type == MedicalStudySearchType.PATIENT_DNI:
        if not patient_dni or not access_code:
            raise HTTPException(
                status_code=400, 
                detail="DNI del paciente y código de acceso son requeridos"
            )
        return study_service.get_by_patient_dni(db, dni=patient_dni, access_code=access_code)
        
    if search_type == MedicalStudySearchType.PATIENT_NAME:
        if not patient_name:
            raise HTTPException(status_code=400, detail="patient_name is required for 'patient_name' search type")
        return study_service.get_by_patient_name(db, name=patient_name)

@router.get("/public-search/", response_model=Union[List[MedicalStudyResponseDTO], MedicalStudyResponseDTO])
def public_search_medical_studies(
    patient_dni: Optional[str] = Query(None, description="DNI del paciente"),
    access_code: Optional[str] = Query(None, description="Código de acceso del paciente"),
    db: Session = Depends(get_db),
    study_service: MedicalStudyService = Depends(get_medical_study_service)
) -> Union[List[MedicalStudyResponseDTO], MedicalStudyResponseDTO]:
    """
    Búsqueda pública de estudios médicos.
    """
    if not patient_dni or not access_code:
        raise HTTPException(
            status_code=400,
            detail="DNI del paciente y código de acceso son requeridos"
        )
    return study_service.get_by_patient_dni(db, dni=patient_dni, access_code=access_code)

@router.delete("/{study_id}", response_model=MessageResponse)
def delete_medical_study(
    study_id: UUID,
    db: Session = Depends(get_db),
    study_service: MedicalStudyService = Depends(get_medical_study_service),
    current_user: UserOut = Depends(get_current_user)
):
    """
    Elimina un estudio médico por su ID.
    """
    study_service.delete_study(db, study_id=study_id)
    return MessageResponse(message="Study deleted successfully")

@router.patch("/{study_id}", response_model=MedicalStudyResponseDTO)
def partial_update_study(
    study_id: UUID,
    study_data: MedicalStudyUpdateDTO, 
    db: Session = Depends(get_db),
    study_service: MedicalStudyService = Depends(get_medical_study_service),
    current_user: UserOut = Depends(get_current_user)
) -> MedicalStudyResponseDTO:
    """
    Actualiza parcialmente un estudio médico existente.
    Solo envía los campos que deseas cambiar en el cuerpo de la petición.
    """
    try:
        updated_study = study_service.update(db, study_id=study_id, study_update=study_data)
        db.commit()
        return updated_study
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))