from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from loguru import logger as log
from ...infrastructure.db.DTOs.auth_schema import UserOut
from ...services.diagnose_service import DiagnoseService
from ...infrastructure.db.DTOs.medical_study_dto import MedicalStudyResponseDTO
from ...services.medical_study_service import MedicalStudyService
from ...services.file_manager_service import FileStorageService
from ...infrastructure.repositories.medical_study_repo import MedicalStudyRepo
from ...infrastructure.repositories.file_manager_repo import FileStorageRepo
from ...infrastructure.repositories.user_repo import UserRepo
from ...core.db import get_db_session as get_db
from ...api.v1.auth import get_current_user

router = APIRouter(prefix="/diagnose", tags=["Diagnosis"])

def get_diagnose_service(db: Session = Depends(get_db)) -> DiagnoseService:
    """
    Construye y provee el servicio de diagnóstico con todas sus dependencias.
    """
    return DiagnoseService(
        study_service=MedicalStudyService(
            medical_study_repo=MedicalStudyRepo(), 
            user_repo=UserRepo(db)  
        ),
        file_service=FileStorageService(
            file_storage_repo=FileStorageRepo()  
        )
    )

@router.post("/{study_id}", response_model=MedicalStudyResponseDTO)
async def perform_diagnosis(
    study_id: UUID,
    user_id: UUID = Form(..., description="ID del técnico/doctor que realiza el diagnóstico."),
    file: UploadFile = File(..., description="Archivo CSV con datos del electromiograma."),
    db: Session = Depends(get_db),
    diagnose_service: DiagnoseService = Depends(get_diagnose_service),
    current_user: UserOut = Depends(get_current_user)
):
    """
    Recibe un CSV para un estudio, ejecuta el pipeline de diagnóstico,
    guarda el archivo y actualiza el estudio con los resultados.
    """
    
    if not file.filename or not file.filename.endswith(('.csv', '.CSV')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files are allowed."
        )
        
    try:
        
        updated_study = await diagnose_service.run_diagnosis_workflow(
            db, study_id=study_id, file=file, user_id=user_id
        )
        
        db.commit() 
        return updated_study
    except Exception as e:
        db.rollback()
        import traceback
        error_trace = traceback.format_exc()
        log.error(f"Unexpected error in diagnose workflow (DiagnoseService): {str(e)}\nTraceback: {error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Unknown error: {str(e)}"
        )