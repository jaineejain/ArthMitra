import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from this package directory (arthmitra/backend/.env) — works no matter where
# you start uvicorn (repo root vs backend folder). CWD-based load_dotenv() alone misses it.
_backend_dir = Path(__file__).resolve().parent
load_dotenv(_backend_dir / ".env")
load_dotenv()  # optional: override from current working directory

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
# Prefer 127.0.0.1 in default to avoid Windows resolving "localhost" to ::1 without password
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://127.0.0.1:5432/arthmitra")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
MFAPI_BASE = os.getenv("MFAPI_BASE", "https://api.mfapi.in/mf")

# JWT auth — set JWT_SECRET in production (min 32 random bytes)
JWT_SECRET = os.getenv("JWT_SECRET", "dev-insecure-change-me-use-openssl-rand-hex-32")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))  # 7 days default

# Comma-separated extra origins for production (e.g. https://app.example.com)
_default_cors = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:4173,http://127.0.0.1:4173,"
    "http://localhost:3000,http://127.0.0.1:3000"
)
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_cors).split(",") if o.strip()]

