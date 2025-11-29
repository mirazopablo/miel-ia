# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ...infrastructure.db.DTOs.auth_schema import Token, UserLogin, UserCreate, UserOut
from ...infrastructure.db.DTOs.user_dto import UserCreateInternal, UserResponseDTO as UserResponse
from ...infrastructure.db.DTOs.user_role_dto import UserRoleCreateDTO
from ...infrastructure.db.models.user_role import UserRole
from ...infrastructure.db.models.user import User
from ...infrastructure.db.models.role import Role
from ...services.user_service import UserService
from ...services.role_service import RoleService
from ...services.user_role_service import UserRoleService
from ...infrastructure.repositories.role_repo import RoleRepo
from ...infrastructure.repositories.user_role_repo import UserRoleRepo
from ...core.config import settings
from jose import jwt
from ...core.db import get_db_session as get_db
from ...services.auth_service import AuthService, get_auth_service, oauth2_scheme
from ...infrastructure.repositories.user_repo import UserRepo
from sqlalchemy.orm import Session

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(user_repo=UserRepo(db))

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> UserOut:
    """Dependency para obtener el usuario actual autenticado."""
    auth_service = get_auth_service(db)
    return auth_service.get_current_user(db, token)

def get_user_role_service(db: Session = Depends(get_db)) -> UserRoleService:
    user_repo = UserRepo(db)  
    role_repo = RoleRepo(db)  
    user_role_repo = UserRoleRepo(db)  
    return UserRoleService(user_role_repo, user_repo, role_repo)

def get_role_repo(db: Session = Depends(get_db)) -> RoleRepo:
    return RoleRepo(db)

def get_role_service(role_repo: RoleRepo = Depends(get_role_repo)) -> RoleService:
    return RoleService(role_repo)

def get_user_repository(db: Session = Depends(get_db)) -> UserRepo:
    return UserRepo(db)

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> UserOut:
    """Dependency para obtener el usuario actual autenticado."""
    auth_service = get_auth_service(db)
    return auth_service.get_current_user(db, token)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"]
)

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
):
    user_login = UserLogin(email=form_data.username, password=form_data.password)
    return auth_service.login(db, user_login)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
    user_role_service: UserRoleService = Depends(get_user_role_service),
    role_service: RoleService = Depends(get_role_service),
):
    """Registrar un nuevo usuario"""
    try:

        all_roles = db.query(Role).all()        
        role = role_service.get_role(user_data.role_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role with ID {user_data.role_id} not found"
            )
        
        user_for_creation = UserCreateInternal.model_validate(user_data)
        user = user_service.create_user(db, user_for_creation)

        user_role_data = UserRoleCreateDTO(user_id=user.id, role_id=user_data.role_id)
        user_role_service.create_user_role(db, obj_in=user_role_data)

        db.commit()
        db.refresh(user)
        return user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred(api/v1/auth/register): {str(e)}"
        )

@router.get("/me/test-token", include_in_schema=settings.ENVIRONMENT == "development")
async def test_token_decoding(token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)):
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development environment"
        )
    """
    Endpoint de prueba para verificar la decodificación del token JWT.
    Devuelve el payload completo del token decodificado.
    SOLO PARA USO EN DESARROLLO/TESTING.
    """
    try:
        decoded_token = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        auth_service = get_auth_service(db)
        user = auth_service.get_current_user(db, token)
        
        return {
            "decoded_token": decoded_token,
            "user_exists": user is not None,
            "user_info": {
                "email": user.email,
                "id": user.id
            } if user else None
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )