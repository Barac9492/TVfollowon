from __future__ import annotations
from fastapi import APIRouter
from app.api.companies import router as companies_router
from app.api.upload import router as upload_router
from app.api.slack import router as slack_router
from app.api.research import router as research_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(companies_router)
api_router.include_router(upload_router)
api_router.include_router(slack_router)
api_router.include_router(research_router)
