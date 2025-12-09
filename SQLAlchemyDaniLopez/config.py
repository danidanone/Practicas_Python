import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

class Config:
    # Aquí el nombre de la variable de entorno es "SECRET_KEY"
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///productos.db')
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# (Opcional) Comprobar que se están cargando bien
print(f"SECRET_KEY: {Config.SECRET_KEY}")
print(f"DATABASE_URI: {Config.SQLALCHEMY_DATABASE_URI}")