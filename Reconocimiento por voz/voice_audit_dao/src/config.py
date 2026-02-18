"""
config.py - Clase Config
Responsabilidad: Leer las variables de entorno del archivo .env
"""
import os
from dotenv import load_dotenv

# Cargar el .env desde la raíz del proyecto
load_dotenv()


class Config:
    """Lee y expone las credenciales de la base de datos desde el .env"""

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "voice_audit_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    @classmethod
    def get_dsn(cls) -> str:
        """Devuelve el DSN (Data Source Name) para psycopg2"""
        return (
            f"host={cls.DB_HOST} "
            f"port={cls.DB_PORT} "
            f"dbname={cls.DB_NAME} "
            f"user={cls.DB_USER} "
            f"password={cls.DB_PASSWORD}"
        )
