from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import time

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Esperar a que PostgreSQL esté listo
time.sleep(5)

# Conectar a postgres por defecto para crear la base de datos si no existe
DEFAULT_DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/postgres"
default_engine = create_engine(DEFAULT_DB_URL)

max_retries = 5
for i in range(max_retries):
    try:
        with default_engine.connect() as conn:
            conn.execute(text("COMMIT"))
            conn.execute(text(f"CREATE DATABASE {POSTGRES_DB}"))
            print(f"Database {POSTGRES_DB} created successfully")
            break
    except Exception as e:
        print(f"Attempt {i+1}/{max_retries}: Database might already exist or not ready: {e}")
        if i < max_retries - 1:
            time.sleep(2)
    finally:
        default_engine.dispose()

# Conectar a la base de datos objetivo
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    import models
    models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()