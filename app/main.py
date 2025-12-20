from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .core.db import get_db_session, check_database_connection

from .api.routes.test_binary import test_binary
from .api.routes.train_binary import train_binary
from .api.routes.train_classify import train_classify
from .api.routes.test_classify import test_classify
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
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Global Exception Handler to ensure tracebacks are visible
from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = f"Global Exception Handler: {str(exc)}"
    log.error(error_msg)
    log.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "debug_message": str(exc)}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

app.include_router(test_binary, tags=["Test"])
app.include_router(test_classify, tags=["Test"])
app.include_router(train_binary, tags=["Train"])
app.include_router(train_classify, tags=["Train"])
app.include_router(user_router)
app.include_router(medical_study_router)
app.include_router(diagnose_router)
app.include_router(auth_router)
app.include_router(role_router)
app.include_router(register_router)
app.include_router(password_recovery_router, prefix="/api/v1/auth", tags=["Auth"])


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