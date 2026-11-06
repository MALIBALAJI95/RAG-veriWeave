"""Health and diagnostics endpoints."""

from fastapi import APIRouter, Depends
from backend.app.api.deps import (
    get_embedding_model,
    get_ollama_client,
    get_settings,
    get_storage_manager,
)
from backend.app.core.config import Settings
from backend.app.embeddings.base import BaseEmbeddings
from backend.app.generation.ollama_client import OllamaClient
from backend.app.schemas.health import ComponentStatus, HealthResponse
from backend.app.storage.qdrant_client import QdrantStorageManager

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="System health status",
    description="Reports the operational status of vector storage, embedding engine, and Ollama LLM.",
)
async def check_health(
    settings: Settings = Depends(get_settings),
    storage: QdrantStorageManager = Depends(get_storage_manager),
    embeddings: BaseEmbeddings = Depends(get_embedding_model),
    ollama: OllamaClient = Depends(get_ollama_client),
) -> HealthResponse:
    components = {}

    # Check Vector Storage
    try:
        col_info = storage.get_collection_info(settings.QDRANT_COLLECTION_NAME)
        components["vector_storage"] = ComponentStatus(
            status="ok",
            details={
                "engine": "Qdrant (persistent disk)",
                "storage_path": str(settings.QDRANT_STORAGE_PATH),
                "collection": settings.QDRANT_COLLECTION_NAME,
                "vectors_count": col_info.get("vectors_count", 0),
                "points_count": col_info.get("points_count", 0),
            },
        )
    except Exception as e:
        components["vector_storage"] = ComponentStatus(
            status="error",
            details={"error": str(e)},
        )

    # Check Embeddings
    try:
        dim = embeddings.dimension
        components["embeddings"] = ComponentStatus(
            status="ok",
            details={
                "model_name": settings.EMBEDDING_MODEL_NAME,
                "dimension": dim,
                "device": settings.EMBEDDING_DEVICE,
            },
        )
    except Exception as e:
        components["embeddings"] = ComponentStatus(
            status="error",
            details={"error": str(e)},
        )

    # Check Ollama LLM
    reachable, ollama_details = ollama.check_health()
    components["llm_engine"] = ComponentStatus(
        status="ok" if reachable else "degraded",
        details=ollama_details,
    )

    overall_status = "healthy"
    if components["vector_storage"].status != "ok" or components["embeddings"].status != "ok":
        overall_status = "unhealthy"
    elif not reachable:
        overall_status = "degraded"

    return HealthResponse(
        app_name=settings.APP_NAME,
        status=overall_status,
        version=settings.APP_VERSION,
        components=components,
    )
