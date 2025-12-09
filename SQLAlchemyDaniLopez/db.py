import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import declarative_base
from config import Config

# Motor de la base de datos
engine = sa.create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=False)

# Sesión
SessionLocal = orm.sessionmaker(bind=engine)
session = SessionLocal()

# Base para los modelos
Base = declarative_base()