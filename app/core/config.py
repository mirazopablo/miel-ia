import os
import time
from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from sqlalchemy import text
from urllib.parse import quote_plus
from loguru import logger as log

load_dotenv()

class Settings(BaseSettings):
    APP: str = "Miel-IA: AI POWERED DIAGNOSIS SYSTEM"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Miel-IA es un sistema de diagnóstico médico impulsado por IA, diseñado para ayudar a los profesionales de la salud a tomar decisiones informadas y precisas."
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    DB_HOST: str
    DB_PORT: str = "3306"
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    DB_DRIVER: str = "mysql+pymysql"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    RESET_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "60"))
    
    # Email Settings
    EMAILS_ENABLED: bool = True
    EMAIL_BACKEND: str = "file"  # Options: "file", "console"
    
    ALLOWED_ORIGINS: Union[str, List[str]] = "*"
    ALLOWED_METHODS: Union[str, List[str]] = "*"
    ALLOWED_HEADERS: Union[str, List[str]] = "*"
    ALLOW_CREDENTIALS: bool = True
    
    WORKERS: int = 1
    RELOAD: bool = True
    
    LOG_LEVEL: str = "DEBUG"
    
    MODELS_PATH: str = "trained_models"
    BINARY_MODELS_PATH: str = "trained_models/binary"
    CLASSIFY_MODELS_PATH: str = "trained_models/classify"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"
    
    @property
    def cors_origins(self) -> List[str]:
        """Convierte ALLOWED_ORIGINS a lista si es necesario"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            if self.ALLOWED_ORIGINS == "*":
                return ["*"]
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        return self.ALLOWED_ORIGINS
    
    @property
    def cors_methods(self) -> List[str]:
        """Convierte ALLOWED_METHODS a lista si es necesario"""
        if isinstance(self.ALLOWED_METHODS, str):
            if self.ALLOWED_METHODS == "*":
                return ["*"]
            return [method.strip() for method in self.ALLOWED_METHODS.split(",") if method.strip()]
        return self.ALLOWED_METHODS
    
    @property
    def cors_headers(self) -> List[str]:
        """Convierte ALLOWED_HEADERS a lista si es necesario"""
        if isinstance(self.ALLOWED_HEADERS, str):
            if self.ALLOWED_HEADERS == "*":
                return ["*"]
            return [header.strip() for header in self.ALLOWED_HEADERS.split(",") if header.strip()]
        return self.ALLOWED_HEADERS
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }
    @property
    def DATABASE_URL(self) -> str:
         encoded_password = quote_plus(self.DB_PASS)
         return f"{self.DB_DRIVER}://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


try:
    settings = Settings()

except Exception as e:
    log.error(f"Error loading configuration: {e}")
