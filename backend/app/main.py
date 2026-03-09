from __future__ import annotations
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging so research_service logs show in Railway
logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")

from app.config import settings
from app.database import engine, Base
from app.api.router import api_router

# Import all models so they are registered with Base
import app.models  # noqa: F401


def _migrate_columns(engine):
    """Add new columns to existing tables if missing (SQLite ALTER TABLE)."""
    import sqlite3
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.exists(db_path):
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Companies table migrations
    cursor.execute("PRAGMA table_info(companies)")
    existing = {row[1] for row in cursor.fetchall()}
    company_migrations = [
        ("has_growth_data", "INTEGER DEFAULT 0"),
        ("growth_data_completeness", "REAL DEFAULT 0.0"),
    ]
    for col_name, col_type in company_migrations:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type}")

    # Growth metrics table migrations
    cursor.execute("PRAGMA table_info(growth_metrics)")
    gm_existing = {row[1] for row in cursor.fetchall()}
    if gm_existing and "investors" not in gm_existing:
        cursor.execute("ALTER TABLE growth_metrics ADD COLUMN investors TEXT")

    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create data directories
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Migrate existing tables
    _migrate_columns(engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
