import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure `import arthmitra...` works when running from `cd arthmitra/backend`.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from arthmitra.backend.config import CORS_ORIGINS, DATABASE_URL
from arthmitra.backend.db_bootstrap import bootstrap_database
from arthmitra.backend.routers.auth import router as auth_router
from arthmitra.backend.routers.chat import router as chat_router
from arthmitra.backend.routers.users import router as users_router
from arthmitra.backend.routers.upload import router as upload_router
from arthmitra.backend.routers.mentor import router as mentor_router


app = FastAPI(title="ArthMitra — AI Money Mentor Pro")

# JWT in Authorization header — credentials not required. Override via CORS_ORIGINS in .env.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(mentor_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0"}


@app.get("/api/health")
def api_health():
    """Hackathon / gateway health — lists core service surfaces."""
    return {
        "status": "ok",
        "services": ["fire", "tax", "mhs", "mentor_v2", "upload", "users"],
    }


@app.on_event("startup")
def startup_create_tables():
    """Apply schema + migrations (email/password_hash, chats, messages). Safe on existing DBs."""
    bootstrap_database(DATABASE_URL)

