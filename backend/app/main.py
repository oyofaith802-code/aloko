import os
from pathlib import Path

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# DATABASE MODELS
# ============================================================

from app.models import (
    User,
    Avatar,
    Voice,
    Video,
    CreatorProject,
    CreatorScene,
)


# ============================================================
# BUSINESS AI MODELS
# ============================================================

from app.business_ai.models import (
    BusinessWorkspace,
    BusinessDataset,
    BusinessMemory,
)


# ============================================================
# ROUTES
# ============================================================

# Authentication
from app.routes.auth import (
    router as auth_router,
)


# Avatars
from app.routes.avatars import (
    router as avatars_router,
)


# Videos
from app.routes.videos import (
    router as videos_router,
)


# Voices
from app.routes.voices import (
    router as voices_router,
)


# Voice Translator
from app.routes.translator import (
    router as translator_router,
)


# Translator locales
from app.routes.translator_locales import (
    router as translator_locales_router,
)


# Creator Projects
from app.routes.projects import (
    router as projects_router,
)


# Creator Rendering
from app.routes.creator_render import (
    router as creator_render_router,
)


# AI Director
from app.routes.ai_director import (
    router as ai_director_router,
)


# University Lecturer
from app.university_ai.routes.lecturer import (
    router as university_lecturer_router,
)


# University Student
from app.university_ai.routes.student_routes import (
    router as university_student_router,
)


# ============================================================
# BUSINESS AI ROUTES
# ============================================================

# Business AI - Datasets
from app.business_ai.routes.datasets import (
    router as business_datasets_router,
)


# Business AI - Workspaces
from app.business_ai.routes.workspaces import (
    router as business_workspaces_router,
)


# Business AI - Analysis
from app.business_ai.routes.analysis import (
    router as business_analysis_router,
)


# Business AI - Reports
from app.business_ai.routes.reports import (
    router as business_reports_router,
)


# Business AI - API
from app.business_ai.routes.business_api import (
    router as business_api_router,
)


# ============================================================
# UNIVERSITY AI ROUTES
# ============================================================

# University Clearance
from app.university_ai.routes.clearance import (
    router as university_clearance_router,
)


# University Payments
from app.university_ai.routes.payments import (
    router as university_payments_router,
)


# University Portal
from app.university_ai.routes.portal import (
    router as university_portal_router,
)


# University Portal Admin
from app.university_ai.routes.portal_admin import (
    router as university_portal_admin_router,
)


# University AI Marking
from app.university_ai.routes.ai_marking import (
    router as university_ai_marking_router,
)


from app.database.connection import Base, engine

# ============================================================
# APP
# ============================================================

# Create any missing ORM tables automatically on startup.
# This is safe because create_all() does not modify existing tables.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Aloko AI Platform",
    description=(
        "Aloko AI creation platform for "
        "AI voices, avatars, videos, "
        "translation and business intelligence."
    ),
    version="1.0.0",
)


# ============================================================
# CUSTOM OPENAPI
# ============================================================
#
# FastAPI/Pydantic currently represents UploadFile as:
#
#     contentMediaType: application/octet-stream
#
# Swagger UI can display this incorrectly as:
#
#     array<string>
#
# We convert that representation to the standard OpenAPI
# binary format so Swagger shows actual file upload controls.
#
# This changes ONLY the generated OpenAPI documentation.
# It does not change the actual upload endpoint behavior.
# ============================================================

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    def fix_upload_schema(value):
        if isinstance(value, dict):

            if value.get("contentMediaType") == "application/octet-stream":
                value.pop("contentMediaType", None)
                value["format"] = "binary"

            for child in value.values():
                fix_upload_schema(child)

        elif isinstance(value, list):
            for child in value:
                fix_upload_schema(child)

    fix_upload_schema(openapi_schema)

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "https://aloko-1.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STORAGE
# ============================================================

STORAGE_DIR = Path("storage")

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# STORAGE SUBDIRECTORIES
# ============================================================

AVATAR_STORAGE_DIR = (
    STORAGE_DIR / "avatars"
)

VIDEO_STORAGE_DIR = (
    STORAGE_DIR / "videos"
)

AUDIO_STORAGE_DIR = (
    STORAGE_DIR / "audio"
)

CREATOR_RENDER_DIR = (
    STORAGE_DIR / "creator_renders"
)

BUSINESS_DATASET_STORAGE_DIR = (
    STORAGE_DIR / "business_datasets"
)


AVATAR_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

VIDEO_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

AUDIO_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

CREATOR_RENDER_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

BUSINESS_DATASET_STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# STATIC STORAGE
# ============================================================

app.mount(
    "/storage",
    StaticFiles(
        directory=str(
            STORAGE_DIR
        )
    ),
    name="storage",
)


# ============================================================
# REGISTER ROUTES
# ============================================================

# ------------------------------------------------------------
# Authentication
# ------------------------------------------------------------

app.include_router(
    auth_router
)


# ------------------------------------------------------------
# Business AI
# ------------------------------------------------------------

app.include_router(
    business_workspaces_router
)

app.include_router(
    business_datasets_router
)

app.include_router(
    business_analysis_router
)

app.include_router(
    business_reports_router
)

app.include_router(
    business_api_router
)


# ------------------------------------------------------------
# Creator AI
# ------------------------------------------------------------

# Avatars
app.include_router(
    avatars_router
)


# Videos
app.include_router(
    videos_router
)


# Voices
app.include_router(
    voices_router
)


# Voice Translator
app.include_router(
    translator_router
)


# Translator locales
app.include_router(
    translator_locales_router
)


# Creator Projects
app.include_router(
    projects_router
)


# Creator Rendering
app.include_router(
    creator_render_router
)


# AI Director
app.include_router(
    ai_director_router
)


# ------------------------------------------------------------
# University AI
# ------------------------------------------------------------

app.include_router(
    university_clearance_router
)

app.include_router(
    university_payments_router
)

app.include_router(
    university_portal_router
)

app.include_router(
    university_portal_admin_router
)

app.include_router(
    university_lecturer_router
)

app.include_router(
    university_student_router
)

app.include_router(
    university_ai_marking_router
)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "name": "Aloko AI Platform",
        "message": "Aloko backend is running.",
        "version": "1.0.0",
        "modules": {
            "creator_ai": True,
            "business_ai": True,
            "ai_director": True,
            "voice_platform": True,
            "translation": True,
        },
        "docs": "/docs",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "aloko-backend",
    }


