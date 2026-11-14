"""
src/api/main.py — FastAPI Application Entrypoint for InterviewDNA.
"""

from __future__ import annotations

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("interviewdna.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload models, vector store, and orchestrator on startup."""
    logger.info("Lifespan startup: Preloading ChromaDB, embeddings, and Orchestrator...")
    try:
        from src.api.deps import get_orchestrator, get_retriever, load_archive_records
        _ = get_retriever()
        _ = get_orchestrator()
        _ = load_archive_records()
        logger.info("Lifespan startup complete: All dependencies preloaded.")
    except Exception as exc:
        logger.error("Lifespan startup preloading error: %s", exc, exc_info=True)
    yield
    logger.info("Lifespan shutdown: Releasing resources.")


app = FastAPI(
    title="InterviewDNA REST API",
    description=(
        "Local API service wrapping InterviewDNA's Agentic RAG architecture, "
        "intent router, dynamic scoring, evidence-grounded coaching, and SQLite persistence."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# CORS Middleware (Frontend at http://localhost:5173)
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Unified Error Handlers {error: str, detail: str}
# -----------------------------------------------------------------------------

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail_str = str(exc.detail) if isinstance(exc.detail, str) else str(exc.detail)
    error_type = "Not Found" if exc.status_code == 404 else "HTTP Error"
    logger.warning("HTTP %d error on %s: %s", exc.status_code, request.url.path, detail_str)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_type, "detail": detail_str},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    err_msgs: list[str] = []
    for err in exc.errors():
        loc = " -> ".join(str(p) for p in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        err_msgs.append(f"{loc}: {msg}")
    full_detail = "; ".join(err_msgs) if err_msgs else str(exc)
    logger.warning("Validation error on %s: %s", request.url.path, full_detail)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation Error", "detail": full_detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )


# -----------------------------------------------------------------------------
# Attach Routes
# -----------------------------------------------------------------------------
app.include_router(router)


@app.get("/", tags=["InterviewDNA"])
async def root():
    """Root redirect / index info."""
    return {
        "service": "InterviewDNA API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/api/health",
    }
