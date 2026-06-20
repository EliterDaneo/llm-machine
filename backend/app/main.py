"""
PDF Intelligence App - FastAPI Entry Point
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.db.database import init_db
from app.api import auth, documents, admin

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG if not settings.is_production else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before serving and cleanup on shutdown."""
    logger.info(f"🚀 Starting {settings.APP_NAME} [{settings.APP_ENV}]")

    # Initialize DB tables on startup (dev only — use Alembic for prod)
    if not settings.is_production:
        try:
            await init_db()
        except Exception as e:
            logger.error(f"DB init failed: {e}")

    logger.info("✅ App ready to serve requests")
    yield
    logger.info("👋 Shutting down...")


# ─────────────────────────────────────────────
# App Instance
# ─────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered PDF analysis platform with Gemini & Groq integration",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

if settings.is_production:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com"])


# ─────────────────────────────────────────────
# Exception Handlers
# ─────────────────────────────────────────────

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return clean validation errors in Indonesian."""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({"field": field, "message": error["msg"]})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Data yang dikirim tidak valid.",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Terjadi kesalahan server. Silakan coba lagi."},
    )


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(admin.router,     prefix="/api/v1")


# ─────────────────────────────────────────────
# Health & Root
# ─────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers / uptime monitors."""
    from app.services.ai_orchestrator import ai_orchestrator
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "ai_providers": ai_orchestrator.get_provider_status(),
    }


# ─────────────────────────────────────────────
# Dev entrypoint
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=not settings.is_production,
        log_level="debug" if not settings.is_production else "info",
    )