# app/db/session.py
import time
from typing import Generator
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from app.core.config import settings

# Try to connect to the database with retries
max_retries = 5
retry_delay = 5  # seconds

for attempt in range(max_retries):
    try:
        engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
        # Test connection
        with engine.connect() as conn:
            pass
        break
    except OperationalError as e:
        if attempt < max_retries - 1:
            print(f"Database connection error: {str(e)}. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("Using SQLite for development as PostgreSQL connection failed")
            # Fallback to SQLite for development
            engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()