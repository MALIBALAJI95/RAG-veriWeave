"""Document management endpoints (upload, list, inspect, delete)."""

from datetime import datetime
from pathlib import Path
from typing import Any, List
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

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/upload",
    response_model=IngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index document",
    description="Uploads a PDF, DOCX, TXT, or MD document. Extracts text, chunks, embeds, and indexes to persistent vector store.",
)
async def upload_document(
    file: UploadFile = File(...),
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
    settings: Settings = Depends(get_settings),
) -> IngestionResponse:
    filename = file.filename or "uploaded_document"
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{ext}'. Supported formats: {list(SUPPORTED_EXTENSIONS.keys())}",
        )

    # Size validation guard
    if file.size and file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed upload size of {max_mb} MB.",
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
    description="Retrieves a list of all documents indexed in persistent vector database.",
)
async def list_documents(
    storage: Any = Depends(get_storage_manager),
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

        # Fallback to database metadata if local disk file does not exist (ephemeral cloud container)
        if file_size == 0:
            try:
                from backend.app.database.session import get_db_session
                from backend.app.database.models import DocumentRecord
                with get_db_session() as session:
                    doc_rec = session.query(DocumentRecord).filter(DocumentRecord.doc_id == doc_id).first()
                    if doc_rec:
                        file_size = doc_rec.file_size_bytes or 0
                        created_at = doc_rec.created_at or created_at
            except Exception:
                pass

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
    storage: Any = Depends(get_storage_manager),
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
    storage: Any = Depends(get_storage_manager),
    settings: Settings = Depends(get_settings),
) -> DocumentDeleteResponse:
    # 1. Delete points from vector store
    deleted_count = storage.delete_document(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        doc_id=doc_id,
    )

    # Sync deletion to structured database
    try:
        from backend.app.database.session import sync_document_deletion, get_db_session
        from backend.app.database.models import DocumentBlobRecord
        sync_document_deletion(doc_id)
        with get_db_session() as session:
            session.query(DocumentBlobRecord).filter(DocumentBlobRecord.doc_id == doc_id).delete()
    except Exception as db_err:
        logger.warning(f"Structured DB deletion sync error: {db_err}")
        from backend.app.database.session import sync_document_deletion
        sync_document_deletion(doc_id)
    except Exception as db_err:
        logger.debug(f"SQLite deletion sync skipped: {db_err}")

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
