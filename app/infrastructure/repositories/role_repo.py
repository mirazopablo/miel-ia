# infrastructure/repositories/role_repo.py
from sqlalchemy.orm import Session
from ...infrastructure.db.models.role import Role
from typing import List, Optional, Any, Union
import uuid
from ...infrastructure.repositories.base_repo import BaseRepository

class RoleRepo(BaseRepository[Role]):
    def __init__(self, db: Session):
        super().__init__(Role, db)

    def get_by_id(self, id: Union[str, uuid.UUID]) -> Optional[Role]:
        """Obtiene el rol completo por su ID (acepta string o UUID)"""
        if isinstance(id, uuid.UUID):
            id = str(id)        
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_role_name(self, id: Union[str, uuid.UUID]) -> Optional[str]:
        """Obtiene solo el nombre del rol (acepta string o UUID)"""
        if isinstance(id, uuid.UUID):
            id = str(id)

        role = self.get_by_id(id)
        return role.name if role else None

    def get(self, db: Session = None, id: Any = None) -> List[Role]:
        """Implementación del método abstracto get de BaseRepository"""
        if id is not None:
            return self.get_by_id(id)
        return self.db.query(self.model).all()

    def create(self, db: Session = None, *, obj_in: Any = None, name: str = None) -> Role:
        """Implementación del método abstracto create de BaseRepository"""
        if name is None and obj_in is not None:
            name = obj_in.name if hasattr(obj_in, 'name') else str(obj_in)
        
        if name is None:
            raise ValueError("Name is required to create a role")
            
        db_obj = self.model(name=name)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_all(self) -> List[Role]:
        """Método específico para obtener todos los roles"""
        return self.db.query(self.model).all()