from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.errors import AppError, app_error_handler
from app.db.session import engine
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import request_id_middleware
from app.api.routers.health import router as health_router
from app.api.routers.documents import router as documents_router
from app.api.routers.evidence import (
    router as evidence_router,
    runs_router as evidence_runs_router,
)
from app.api.routers.runs import router as runs_router
from app.api.routers.findings import router as findings_router
from app.api.routers.cases import router as cases_router

app = FastAPI(
    title=settings.app_name,
    description="Agentic document intelligence platform",
    version=settings.app_version,
)
app.middleware("http")(request_id_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AppError, app_error_handler)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(evidence_router)
app.include_router(evidence_runs_router)
app.include_router(runs_router)
app.include_router(findings_router)
app.include_router(cases_router)


@app.get("/ready")
async def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ready",
            "database": "connected",
        }

    except SQLAlchemyError:
        raise AppError(
            code="DATABASE_ERROR",
            message="Database is unavailable",
            status_code=503,
        )