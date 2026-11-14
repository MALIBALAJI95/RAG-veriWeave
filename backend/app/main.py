"""FastAPI application entrypoint for VeriWeave."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.app.api.deps import get_settings, get_storage_manager
from backend.app.api.v1.api import api_router
from backend.app.core.exceptions import VeriWeaveException, veriweave_exception_handler
from backend.app.core.logging import get_logger, setup_logging

settings = get_settings()
setup_logging(log_level=settings.LOG_LEVEL)
logger = get_logger("veriweave.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan management."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.APP_TAGLINE})")
    settings.ensure_directories()

    # Pre-warm storage manager and ensure collections
    try:
        storage = get_storage_manager()
        logger.info("Vector storage engine pre-warmed and verified.")
    except Exception as e:
        logger.warning(f"Storage pre-warm check warning (will retry on request): {e}")

    yield

    logger.info("VeriWeave backend shut down cleanly.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        f"**VeriWeave** — Adaptive Multi-Strategy Retrieval and Grounded Generation Engine.\n\n"
        f"*{settings.APP_TAGLINE}*"
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Dynamic CORS Middleware supporting wildcards and custom cloud origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_auth_middleware(request: Request, call_next):
    """Optional API key access protection for cloud deployments."""
    if settings.VERIWEAVE_API_KEY:
        path = request.url.path
        # Whitelist public documentation and health check probes
        if path in ("/", "/docs", "/redoc", "/openapi.json") or path.endswith("/health"):
            return await call_next(request)
        api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        if api_key != settings.VERIWEAVE_API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Invalid or missing X-API-Key header"},
            )
    return await call_next(request)

# Exception handlers
app.add_exception_handler(VeriWeaveException, veriweave_exception_handler)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint welcoming clients."""
    return JSONResponse(
        content={
            "app": settings.APP_NAME,
            "tagline": settings.APP_TAGLINE,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
