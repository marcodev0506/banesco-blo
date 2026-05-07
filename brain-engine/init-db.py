import os
from sqlalchemy import create_engine, text

# Connect to default postgres database to create the target database
DEFAULT_DB_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@db:5432/postgres"
engine = create_engine(DEFAULT_DB_URL)

with engine.connect() as conn:
    conn.execute(text("COMMIT"))
    conn.execute(text(f"CREATE DATABASE {os.getenv('POSTGRES_DB')}"))
    conn.close()

print(f"Database {os.getenv('POSTGRES_DB')} created successfully")
