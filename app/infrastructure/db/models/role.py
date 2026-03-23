from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.associationproxy import association_proxy
from .base_model import BaseModel

class Role(BaseModel):
    __tablename__ = "roles"
    
    """Tabla para almacenar roles de usuario"""
    name: str = Column(String(50), unique=True, nullable=False)
    user_associations = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    users = association_proxy("user_associations", "user")
