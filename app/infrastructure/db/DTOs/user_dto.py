from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import EmailStr, Field, field_validator, ConfigDict
from uuid import UUID
from .role_dto import RoleBaseDTO as RoleDTO
from .base_dto import BaseDTO

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class UserBaseDTO(BaseDTO):
    name: str = Field(..., min_length=3, max_length=50, example="johndoe")
    email: EmailStr = Field(..., example="user@example.com")

class UserCreateDTO(UserBaseDTO):
    password: str = Field(..., min_length=8, max_length=100)
    dni: str = Field(..., min_length=8, max_length=20)
    last_name: Optional[str] = Field(None, max_length=100)
    role_id: UUID = Field(..., description="ID del rol asignado")

    @field_validator('name')
    @classmethod
    def name_alphanumeric(cls, v):
        if not v.replace(" ", "").isalnum():
            raise ValueError('El nombre debe contener solo letras, números y espacios')
        return v

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

class UserUpdateDTO(BaseDTO):
    email: Optional[EmailStr] = Field(None)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    dni: Optional[str] = Field(None, min_length=8, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role_id: Optional[UUID] = Field(None)

class UserResponseDTO(UserBaseDTO):
    id: UUID
    dni: str
    name: str
    last_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    roles: List[RoleDTO] = Field(default_factory=list)

class UserLoginDTO(BaseDTO):
    name: str = Field(..., example="johndoe")
    password: str = Field(..., example="securepassword123")

class UserPasswordResetDTO(BaseDTO):
    new_password: str = Field(..., min_length=8, max_length=100)
    token: str = Field(..., description="Token de verificación")

class UserMinimalResponseDTO(BaseDTO):
    id: UUID
    username: str
    email: str

class UserCreateInternal(BaseDTO):
    name: str
    last_name: str
    email: EmailStr
    dni: str
    password: str

class PatientInfoDTO(BaseDTO):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    last_name: str
    dni: str
    email: Optional[EmailStr] = None  

class DoctorInfoDTO(BaseDTO):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    last_name: str
    dni: str
    email: Optional[EmailStr] = None  

class TechnicianInfoDTO(BaseDTO):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    last_name: str
    dni: str
    email: Optional[EmailStr] = None 