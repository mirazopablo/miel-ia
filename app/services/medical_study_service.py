from uuid import UUID
from sqlalchemy.orm import Session, joinedload 
from sqlalchemy import or_
from ..infrastructure.db.models.medical_study import MedicalStudy
from ..infrastructure.db.models.user import User
from fastapi import HTTPException, logger, status
from typing import List, Optional

from ..infrastructure.repositories.medical_study_repo import MedicalStudyRepo
from ..infrastructure.repositories.user_repo import UserRepo
from ..infrastructure.db.DTOs.medical_study_dto import MedicalStudyCreateDTO, MedicalStudyUpdateDTO, MedicalStudyResponseDTO


class MedicalStudyService:
    def __init__(self, medical_study_repo: MedicalStudyRepo, user_repo: UserRepo):
        self.__medical_study_repo = medical_study_repo
        self.__user_repo = user_repo

    def create_study(self, db: Session, study_data: MedicalStudyCreateDTO):
        """
        Crea un nuevo estudio médico con validaciones.
        """
        if self.__medical_study_repo.get_by_access_code(db, access_code=study_data.access_code):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Medical Study Service: Access code already exists."
            )

        doctor = self.__user_repo.get(db, id=study_data.doctor_id)
        if not doctor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Medical Study Service: Doctor not found.")
        
        admin_role_id, doctor_role_id, patient_role_id = self.__get_role_ids_from_db(db)
        
        doctor_role_ids = [str(role.id) for role in doctor.roles]
        doctor_role_names = [role.name for role in doctor.roles]
        
        
        has_doctor_role = (
            "Doctor" in doctor_role_names or 
            str(doctor_role_id) in doctor_role_ids
        )
        
        if not has_doctor_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Medical Study Service: User is not a doctor. User has roles: {doctor_role_names}"
            )
        
        patient = self.__user_repo.get(db, id=study_data.patient_id)
        if not patient:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Medical Study Service: Patient not found.")
        
        patient_role_ids = [str(role.id) for role in patient.roles]
        patient_role_names = [role.name for role in patient.roles]

        has_patient_role = (
            "Patient" in patient_role_names or 
            str(patient_role_id) in patient_role_ids
        )
        
        if not has_patient_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Medical Study Service: User is not a patient. User has roles: {patient_role_names}"
            )

        if study_data.technician_id:
            technician = self.__user_repo.get(db, id=study_data.technician_id)
            if not technician:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Medical Study Service: Technician not found.")

        try:
            study_dict = study_data.model_dump()
            study = self.__medical_study_repo.create(db, obj_in=study_dict)
            log.success(f"Medical Study created successfully (MedicalStudyService)")
            return MedicalStudyResponseDTO.model_validate(study)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Medical Study Service: Error creating medical study, backend error: " + str(e)
            )

    def __get_role_ids_from_db(self, db: Session):
        """
        Obtiene los IDs reales de roles desde la base de datos
        """
        try:
            from ..infrastructure.db.models.role import Role
            roles = db.query(Role).all()
            
            role_map = {}
            for role in roles:
                role_map[role.name] = role.id
            
            return (
                role_map.get('Admin'),
                role_map.get('Doctor'), 
                role_map.get('Patient'),
                role_map.get('Technician')
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching roles from database: " + str(e)
            )



    def get_by_id(self, db: Session, study_id: UUID) -> Optional[MedicalStudyResponseDTO]:
        """
        Obtiene un estudio médico por ID y lo convierte a DTO.
        """
        
        try:
            study = db.query(MedicalStudy).options(
                joinedload(MedicalStudy.patient),
                joinedload(MedicalStudy.doctor),
                joinedload(MedicalStudy.technician)
            ).filter(MedicalStudy.id == str(study_id)).first()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching medical study from database: " + str(e)
            )

        
        try:
            study_dict = {
                "id": study.id,
                "access_code": study.access_code,
                "status": study.status,
                "creation_date": study.created_at, 
                "ml_results": study.ml_results,
                "clinical_data": study.clinical_data,
                "csv_file_id": study.csv_file_id,
                "patient": study.patient,
                "doctor": study.doctor,
                "technician": study.technician
            }
            
            dto = MedicalStudyResponseDTO(**study_dict)
            return dto
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error converting medical study to DTO (MedicalStudyService): " + str(e)
            )
    
    def get_by_patient_dni(self, db: Session, *, dni: str, access_code: str) -> List[MedicalStudy]:
        """
        Obtiene estudios por DNI del paciente con validación de código de acceso.
        """
        if not dni or not access_code:
            raise ValueError("DNI y código de acceso son requeridos (MedicalStudyService)")
        
        dni = dni.strip().replace("-", "").replace(".", "")
        
        studies = self.__medical_study_repo.get_by_patient_dni_and_access_code(db, dni, access_code)

        if not studies:
            raise HTTPException(
                status_code=404, 
                detail="No se encontraron estudios o credenciales inválidas (MedicalStudyService)"
            )
        
        return studies
    def get_by_patient_name(self, db: Session, *, name: str) -> List[MedicalStudy]:
        """
        Busca estudios por nombre o apellido del paciente.
        Es insensible a mayúsculas/minúsculas.
        """
        search_term = f"%{name}%"
        return (
            db.query(self.model)
            .join(User, self.model.patient_id == User.id)
            .filter(
                or_(
                    User.name.ilike(search_term),
                    User.last_name.ilike(search_term)
                )
            )
            .all()
        )
    
    def get_all_studies(self, db: Session) -> List[MedicalStudyResponseDTO]:
        """
        Obtiene todos los estudios médicos y los convierte a DTO.
        """
        studies = self.__medical_study_repo.get_all(db)
        
        return [
            MedicalStudyResponseDTO.model_validate(study) 
            for study in studies
        ]

    def delete_study(self, db: Session, study_id: UUID):
        """
        Verifica que un estudio exista y luego lo elimina.
        """
        study_to_delete = self.get_by_id(db, study_id=study_id)
        log.success(f"Study deleted successfully (MedicalStudyService)")
        return self.__medical_study_repo.delete(db, id=study_to_delete.id)

    def update(self, db: Session, *, study_id: UUID, study_update: MedicalStudyUpdateDTO):
        """
        Actualiza un estudio médico de forma parcial (PATCH).
        """
        db_study = self.__medical_study_repo.get_by_id(db, id=study_id)
        if not db_study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medical study with ID {study_id} not found.(MedicalStudyService)"
            )
        
        update_data = study_update.model_dump(exclude_unset=True)
        log.success(f"Study updated successfully (MedicalStudyService)")

        if "doctor_id" in update_data:
            new_doctor_id = update_data["doctor_id"]
            log.success(f"Doctor ID updated successfully (MedicalStudyService)")
            doctor = self.__user_repo.get(db, id=new_doctor_id)
            if not doctor or "DOCTOR" not in [role.name for role in doctor.roles]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid new Doctor ID: {new_doctor_id}(MedicalStudyService)")
        

        updated_study = self.__medical_study_repo.update(db, db_obj=db_study, obj_in=update_data)
        log.success(f"Study updated successfully (MedicalStudyService)")
        return MedicalStudyResponseDTO.model_validate(updated_study)