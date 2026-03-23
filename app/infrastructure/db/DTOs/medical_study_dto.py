from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from .user_dto import DoctorInfoDTO, PatientInfoDTO
from .base_dto import BaseDTO

TechnicianInfoDTO = DoctorInfoDTO

class MedicalStudyCreateDTO(BaseDTO):
    access_code: str = Field(..., description="Código de acceso único")
    doctor_id: UUID = Field(..., description="ID del médico solicitante")
    patient_id: UUID = Field(..., description="ID del paciente")
    technician_id: Optional[UUID] = Field(None, description="ID del técnico")
    clinical_data: Optional[str] = Field(None, description="Datos clínicos iniciales")

class MedicalStudyUpdateDTO(BaseDTO):
    access_code: Optional[str] = None
    doctor_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    technician_id: Optional[UUID] = None
    clinical_data: Optional[str] = None
    status: Optional[str] = None
    ml_results: Optional[str] = None
    csv_file_id: Optional[UUID] = None

class MedicalStudyResponseDTO(BaseDTO):
    model_config = ConfigDict(from_attributes=True)  
    
    id: UUID
    access_code: str
    status: str
    creation_date: Optional[datetime] = Field(default=None, alias="created_at")
    ml_results: Optional[str] = None
    clinical_data: Optional[str] = None
    csv_file_id: Optional[UUID] = None  

    patient: PatientInfoDTO
    doctor: Optional[DoctorInfoDTO] = None
    technician: Optional[TechnicianInfoDTO] = None