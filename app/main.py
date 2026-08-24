from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # <-- Importar StaticFiles
from contextlib import asynccontextmanager

from .core.config import settings
from .core.db import get_db_session, check_database_connection

from .api.routes.train_binary import train_binary
from .api.routes.train_classify import train_classify
from .api.routes.user import router as user_router
from .api.routes.medical_study import router as medical_study_router
from .api.routes.diagnose import router as diagnose_router
from .api.v1.auth import router as auth_router
from .api.v1.role import router as role_router
from .api.v1.register import router as register_router
from .api.v1.password_recovery import router as password_recovery_router
from loguru import logger as log


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Evento de startup y shutdown de la aplicación
    """

    try:
        db_connected = check_database_connection()
        if db_connected:
            pass
        else:
            if settings.is_development:
                log.warning("DB connection failed, continuing in development mode without DB.")
            else:
                log.error("Database required in production mode")
    except Exception as e:
        if settings.is_development:
            log.warning("🔧 Continuing in development mode...")
        else:
            log.error(f"Database connection failed: {str(e)}")
    
    yield

app = FastAPI(
    title=settings.APP,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan # Añadir lifespan al constructor de FastAPI
)

# Global Exception Handler to ensure tracebacks are visible
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for error in exc.errors():
        # Get the field name, usually loc is like ('body', 'password')
        field = ".".join(str(loc) for loc in error["loc"][1:]) if len(error["loc"]) > 1 else str(error["loc"][0])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")
    
    friendly_message = "Error de validación: " + " | ".join(error_messages)
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "message": friendly_message
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Global Exception Handler: {str(exc)}"
    log.error(error_msg)
    log.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "debug_message": str(exc), "message": "Error interno del servidor"}
    )

# Configuración explícita de CORS antes de instanciar el middleware
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "file://",
    settings.FRONTEND_URL,
    "https://miel-ia.pablomirazo.com.ar"
]

# Fusionar con los orígenes provistos en las variables de entorno, descartando comodines
if isinstance(settings.ALLOWED_ORIGINS, list):
    origins.extend([o for o in settings.ALLOWED_ORIGINS if o != "*"])
elif isinstance(settings.ALLOWED_ORIGINS, str) and settings.ALLOWED_ORIGINS != "*":
    origins.extend([o.strip() for o in settings.ALLOWED_ORIGINS.split(",")])

# Evitar duplicados
origins = list(set(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Montar la carpeta 'static' para servir archivos estáticos (como imágenes de banners)
import os
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Incluir routers
app.include_router(train_binary, tags=["Binary ML Model Training"])
app.include_router(train_classify, tags=["Classification ML Model Training"])
app.include_router(user_router, tags=["Users"])
app.include_router(medical_study_router, tags=["Medical Studies"])
app.include_router(diagnose_router, tags=["Diagnose"])
app.include_router(auth_router, tags=["Authentication"])
app.include_router(role_router, tags=["Roles"])
app.include_router(register_router, tags=["Register"])
app.include_router(password_recovery_router, tags=["Password Recovery"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de health check para monitoreo
    """
    db_status = check_database_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION
    }

def get_db():
    """
    Dependency para inyectar sesión de base de datos
    """
    return get_db_session()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=False,  
        workers=1,
        log_level=settings.LOG_LEVEL.lower()
    )