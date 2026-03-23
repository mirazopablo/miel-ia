from sqlalchemy import create_engine, text
from logging.config import fileConfig
from urllib.parse import quote_plus
from sqlalchemy import engine_from_config
from sqlalchemy import pool
import sys
from alembic import context
import os
from dotenv import load_dotenv

# Añadir la carpeta raíz del proyecto al path para importar módulos app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
load_dotenv()

# Obtener la URL desde la variable de entorno
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT", "3306")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASS")
db_driver = os.getenv("DB_DRIVER", "postgresql+psycopg2")

# Verificar que tenemos todas las variables necesarias
if not all([db_host, db_name, db_user, db_password]):
    missing = []
    if not db_host: missing.append("DB_HOST")
    if not db_name: missing.append("DB_NAME") 
    if not db_user: missing.append("DB_USER")
    if not db_password: missing.append("DB_PASS")
    raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")

# Codificar la contraseña
encoded_password = quote_plus(str(db_password))
database_url = f"{db_driver}://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"

# Configuración de Alembic
config = context.config

# ✅ SOLUCIÓN: Configurar la URL directamente sin usar set_main_option
# En lugar de config.set_main_option, la pasamos directamente al engine

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importar los modelos
try:
    from app.core.db import Base
    from app.infrastructure.db.models.user import User
    from app.infrastructure.db.models.role import Role
    from app.infrastructure.db.models.user_role import UserRole
    from app.infrastructure.db.models.medical_study import MedicalStudy
    from app.infrastructure.db.models.file_manager import FileStorage
    print("✅ Modelos importados correctamente")
except ImportError as e:
    print(f"⚠️  Error importando modelos: {e}")
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    print("✅ Usando Base declarativa básica")

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # ✅ Usar nuestra database_url directamente
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # ✅ Crear engine directamente con nuestra URL
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    
    with connectable.connect() as connection:

        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True
        )
        
        with context.begin_transaction():
            context.run_migrations()
        


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()