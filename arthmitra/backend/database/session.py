from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from arthmitra.backend.config import DATABASE_URL

engine = None
SessionLocal = None

try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception:
    # Allows importing the app even if Postgres dependencies aren't installed yet.
    engine = None
    SessionLocal = None


def get_db():
    if SessionLocal is None:
        # Yield None; endpoints wrap with try/except and return friendly errors.
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

