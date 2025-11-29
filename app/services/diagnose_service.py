import json
import pathlib
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from uuid import UUID
from .medical_study_service import MedicalStudyService
from .file_manager_service import FileStorageService
from ..infrastructure.db.DTOs.medical_study_dto import MedicalStudyUpdateDTO
from ..ml_pipeline.pipeline import run_diagnosis_pipeline
from loguru import logger as log


class DiagnoseService:
    def __init__(self, study_service: MedicalStudyService, file_service: FileStorageService):
        self.__study_service = study_service
        self.__file_service = file_service

    async def run_diagnosis_workflow(self, db: Session, study_id: UUID, file: UploadFile, user_id: UUID):
        try:
            print(f"🔍 DiagnoseService - Buscando estudio: {study_id}")
            
            # PRIMERO: Usar el servicio para obtener el estudio (que usa la consulta directa)
            study_dto = self.__study_service.get_by_id(db, study_id=study_id)
            
            if not study_dto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Medical study with ID {study_id} not found.(DiagnoseService)"
                )
                        
            from sqlalchemy.orm import joinedload
            from ..infrastructure.db.models.medical_study import MedicalStudy
            
            study_model = db.query(MedicalStudy).options(
                joinedload(MedicalStudy.patient),
                joinedload(MedicalStudy.doctor),
                joinedload(MedicalStudy.technician)
            ).filter(MedicalStudy.id == study_id).first()
            
            if not study_model:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Internal server error: data inconsistency (DiagnoseService)"
                )
            
            if study_model.status != "PENDING":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Medical study with ID {study_id} is not in PENDING state. Current status: {study_model.status}(DiagnoseService)"
                )

            if not study_model.patient:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Patient not found for this study(DiagnoseService)"
                )

            patient = study_model.patient
            study_date_str = study_model.created_at.strftime('%Y%m%d')
            original_extension = pathlib.Path(file.filename).suffix
            new_filename = f"{patient.id}_{patient.name}_{patient.last_name}_{study_date_str}{original_extension}".replace(" ", "_")
            
            saved_file = await self.__file_service.save_file_to_db(
                db, 
                file=file, 
                user_id=user_id, 
                patient_dni=patient.dni, 
                custom_filename=new_filename
            )
        
            try:
                await file.seek(0)
                ml_verdict = run_diagnosis_pipeline(file.file)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Bad Request raised for DiagnoseService: {str(e)}')
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"ML processing error (DiagnoseService): {str(e)}")

            update_data = MedicalStudyUpdateDTO(
                status="COMPLETED",
                ml_results=json.dumps(ml_verdict),
                csv_file_id=saved_file.id
            )
            
            updated_study = self.__study_service.update(db, study_id=study_id, study_update=update_data)
            log.success(f"Study updated successfully (DiagnoseService)")
            return updated_study
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"❌ Unexpected error in diagnose workflow (DiagnoseService): {e}")
            import traceback
            log.error(f"🔍 Traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal server error (DiagnoseService): {str(e)}"
            )