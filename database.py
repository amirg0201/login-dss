from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import Base
import os

# Cargar variables desde .env
if os.getenv("FLASK_ENV") != "production":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️ python-dotenv no está instalado. Si estás en producción, esto es normal.")


# Leer la URL de la base de datos desde la variable de entorno
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("La variable de entorno DATABASE_URL no está definida.")

# Crear motor y sesión
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Crear las tablas si no existen
def init_db():
    Base.metadata.create_all(bind=engine)
