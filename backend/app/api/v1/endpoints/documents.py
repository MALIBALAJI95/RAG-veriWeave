"""Document management endpoints (upload, list, inspect, delete)."""

from datetime import datetime
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from backend.app.api.deps import get_ingestion_pipeline, get_settings, get_storage_manager
from backend.app.core.config import Settings
from backend.app.core.exceptions import DocumentNotFoundError, UnsupportedFileTypeError
from backend.app.core.logging import get_logger
from backend.app.ingestion.loaders.factory import SUPPORTED_EXTENSIONS
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.schemas.document import (
    DocumentChunk,
    DocumentDeleteResponse,
    DocumentDetail,
    DocumentListResponse,
    IngestionResponse,
)
from backend.app.storage.qdrant_client import QdrantStorageManager

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index document",
    description="Uploads a PDF, DOCX, TXT, or MD document. Extracts text, chunks, embeds, and indexes to persistent Qdrant.",
)
async def upload_document(
    file: UploadFile = File(...),
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
) -> IngestionResponse:
    filename = file.filename or "uploaded_document"
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{ext}'. Supported formats: {list(SUPPORTED_EXTENSIONS.keys())}",
        )

    try:
        response = pipeline.ingest_file_stream(
            file_stream=file.file,
            filename=filename,
        )
        return response
    except Exception as e:
        logger.error(f"Upload failed for {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest document: {str(e)}",
        )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all indexed documents",
    description="Retrieves a list of all documents indexed in the persistent Qdrant vector database.",
)
async def list_documents(
    storage: QdrantStorageManager = Depends(get_storage_manager),
    settings: Settings = Depends(get_settings),
) -> DocumentListResponse:
    raw_docs = storage.list_documents(collection_name=settings.QDRANT_COLLECTION_NAME)

    doc_details: List[DocumentDetail] = []
    for d in raw_docs:
        doc_id = d["doc_id"]
        # Find matching file on disk for file size & modification time
        matching_files = list(settings.DOCUMENTS_DIR.glob(f"{doc_id}_*"))
        file_size = matching_files[0].stat().st_size if matching_files else 0
        created_at = (
            datetime.fromtimestamp(matching_files[0].stat().st_ctime)
            if matching_files
            else datetime.utcnow()
        )

        doc_details.append(
            DocumentDetail(
                doc_id=doc_id,
                filename=d["filename"],
                file_type=d["file_type"],
                file_size_bytes=file_size,
                page_count=d["page_count"],
                chunk_count=d["chunk_count"],
                created_at=created_at,
            )
        )

    return DocumentListResponse(total=len(doc_details), documents=doc_details)


@router.get(
    "/{doc_id}",
    response_model=List[DocumentChunk],
    summary="Get document chunks",
    description="Retrieves all indexed text chunks and metadata for a specific document ID.",
)
async def get_document_chunks(
    doc_id: str,
    storage: QdrantStorageManager = Depends(get_storage_manager),
    settings: Settings = Depends(get_settings),
) -> List[DocumentChunk]:
    chunks = storage.get_document_chunks(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        doc_id=doc_id,
    )
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No chunks found for document ID '{doc_id}'",
        )
    return chunks


@router.delete(
    "/{doc_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete indexed document",
    description="Removes document chunks from persistent vector storage and deletes the saved file from disk.",
)
async def delete_document(
    doc_id: str,
    storage: QdrantStorageManager = Depends(get_storage_manager),
    settings: Settings = Depends(get_settings),
) -> DocumentDeleteResponse:
    # 1. Delete points from Qdrant
    deleted_count = storage.delete_document(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        doc_id=doc_id,
    )

    # 2. Delete file from local documents directory if present
    filename = None
    matching_files = list(settings.DOCUMENTS_DIR.glob(f"{doc_id}_*"))
    for f in matching_files:
        filename = f.name.replace(f"{doc_id}_", "")
        f.unlink(missing_ok=True)
        logger.info(f"Removed file from disk: {f.name}")

    if deleted_count == 0 and not matching_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID '{doc_id}' not found in storage.",
        )

    return DocumentDeleteResponse(
        doc_id=doc_id,
        filename=filename,
        chunks_deleted=deleted_count,
        status="deleted",
        message="Document successfully removed from vector storage and disk.",
    )
