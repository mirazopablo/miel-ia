import uuid
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from loguru import logger as log
from ..infrastructure.repositories.file_manager_repo import FileStorageRepo
from ..infrastructure.db.DTOs.file_manager_dto import FileStorageBaseDTO, FileStorageResponseDTO

class FileStorageService:
    def __init__(self, file_storage_repo: FileStorageRepo):
        self.__file_storage_repo = file_storage_repo

    async def save_file_to_db(
        self, 
        db: Session, 
        file: UploadFile, 
        user_id: UUID, 
        patient_dni: str,
        custom_filename: Optional[str] = None,
        description: Optional[str] = None
    ) -> FileStorageResponseDTO:
        """
        Guarda un archivo en el sistema de archivos y registra la metadata en la base de datos.
        
        Args:
            db: Session de base de datos
            file: Archivo a guardar
            user_id: UUID del usuario que sube el archivo
            patient_dni: DNI del paciente para organizar carpetas
            custom_filename: Nombre personalizado para el archivo (opcional)
            description: Descripción del archivo (opcional)
        
        Returns:
            FileStorageResponseDTO: Información del archivo guardado
        """
        import os
        from datetime import datetime
        
        try:
            base_upload_dir = os.path.expanduser("~/uploads")
            patient_dir = os.path.join(base_upload_dir, str(patient_dni))
            
            os.makedirs(patient_dir, exist_ok=True)
            
            if custom_filename:
                filename = custom_filename
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{file.filename}"
                
            file_path = os.path.join(patient_dir, filename)
            
            file_content = await file.read()
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            file_data = FileStorageBaseDTO(
                filename=filename,
                original_filename=file.filename,
                file_type=file.content_type or 'application/octet-stream',
                file_size=len(file_content),
                file_content_binary=None,
                file_path=file_path,
                description=description,
                user_id=user_id
            )
            
            saved_file = self.__file_storage_repo.create(db, obj_in=file_data.model_dump())
            log.success(f"File saved successfully (FileManagerService)")
            return FileStorageResponseDTO.model_validate(saved_file)
            
        except Exception as e:
            log.error(f"Error saving file (FileManagerService): {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file (FileManagerService): {str(e)}"
            )

    def get_file_by_id(self, db: Session, file_id: UUID) -> Optional[FileStorageResponseDTO]:
        """
        Obtiene un archivo por su ID.
        """
        file_record = self.__file_storage_repo.get(db, id=file_id)
        if not file_record:
            log.error(f"File not found (FileManagerService)")
            return None
        
        log.success(f"File found successfully (FileManagerService)")
        return FileStorageResponseDTO.model_validate(file_record)

    def delete_file(self, db: Session, file_id: UUID, user_id: UUID) -> bool:
        """
        Elimina un archivo (solo el propietario puede eliminarlo).
        """
        file_record = self.__file_storage_repo.get(db, id=file_id)
        if not file_record:
            log.error(f"File not found (FileManagerService)")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        if file_record.user_id != user_id:
            log.error(f"Not authorized to delete this file (FileManagerService)")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this file"
            )
        
        self.__file_storage_repo.delete(db, id=file_id)
        log.success(f"File deleted successfully (FileManagerService)")
        return True