from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# URL de conexion
SQLALCHEMY_DATABASE_URL = "sqlite:///./sistema_aprendices.db"

#creamos el motor
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

#creamos la sesión y la unimos al motor
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# La clase de donde saldrán todas las tablas
Base = declarative_base()