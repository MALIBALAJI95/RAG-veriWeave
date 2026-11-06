"""FastAPI application entrypoint for VeriWeave."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
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
    storage = get_storage_manager()
    logger.info(f"Persistent Qdrant storage verified at: {settings.QDRANT_STORAGE_PATH}")

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

# CORS Middleware for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
