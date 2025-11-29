from typing import Any, List
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..infrastructure.db.DTOs.user_dto import UserCreateInternal, UserUpdateDTO, UserBaseDTO
from ..infrastructure.repositories.user_repo import UserRepo
from ..core.security import get_password_hash


class UserService:
    def __init__(self, user_repo: UserRepo):
        self.__user_repo = user_repo

    #Get Methods
    def find_all(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[UserBaseDTO]:
        """Llama al repo para obtener todos los usuarios."""
        users = self.__user_repo.get_all(db, skip=skip, limit=limit)
        return users

    def find_by_id(self, db: Session, user_id: uuid.UUID) -> UserBaseDTO:
        """Busca un usuario por UUID, si no lo encuentra, lanza error 404."""
        user = self.__user_repo.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found (UserService)"
            )
        return user

    def find_by_name(self, db: Session, name: str) -> List[UserBaseDTO]:
        """Busca usuarios por nombre. Devuelve una lista vacía si no hay coincidencias."""
        users = self.__user_repo.get_by_name(db, name=name)
        return users

    def find_by_dni(self, db: Session, dni: str) -> UserBaseDTO:
        """Busca un usuario por DNI, si no lo encuentra, lanza error 404."""
        user = self.__user_repo.get_by_dni(db, dni=dni)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with DNI {dni} not found (UserService)"
            )
        return user
    
    def find_by_email(self, db: Session, email: str) -> UserBaseDTO:
        """Busca un usuario por email, si no lo encuentra, lanza error 404."""
        user = self.__user_repo.get_by_email(db, email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found (UserService)"
            )
        return user


    def create_user(self, db: Session, user_create: UserCreateInternal) -> UserBaseDTO:
        """Crea un nuevo usuario."""
        if self.__user_repo.email_exists(db, email=user_create.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered (UserService)"
            )        
        if self.__user_repo.dni_exists(db, dni=user_create.dni):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="DNI already registered (UserService)"
            )
        
        hashed_password = get_password_hash(user_create.password)
        user_data = user_create.model_dump()
        user_data["password"] = hashed_password

        return self.__user_repo.create(db, obj_in=user_data)

    def update(self, db: Session, user_id: uuid.UUID, user_update: UserUpdateDTO) -> UserBaseDTO:
        """Actualiza un usuario."""
        db_user = self.find_by_id(db, user_id) 
        if user_update.email and user_update.email != db_user.email:
            if self.__user_repo.email_exists(db, email=user_update.email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered by another user (UserService)"
                )
        
        if user_update.dni and user_update.dni != db_user.dni:
            if self.__user_repo.dni_exists(db, dni=user_update.dni):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="DNI already registered by another user (UserService)"
                )

        return self.__user_repo.update(db, db_obj=db_user, obj_in=user_update)
    
    def delete(self, db: Session, user_id: uuid.UUID) -> UserBaseDTO:
        """Elimina un usuario y todas sus relaciones asociadas (vía repositorio)."""
        user = self.find_by_id(db, user_id)
        try:
            deleted_user = self.__user_repo.delete_with_relations(db, id=user_id)
            return deleted_user
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found (UserService)"
            )
        except RuntimeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting user with id {user_id}: {str(e)} (UserService)"
            )
