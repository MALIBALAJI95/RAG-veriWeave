"""End-to-end document ingestion pipeline."""

import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Optional
from backend.app.core.exceptions import DocumentIngestionError
from backend.app.core.logging import get_logger
from backend.app.embeddings.base import BaseEmbeddings
from backend.app.ingestion.chunkers.recursive_chunker import RecursiveCharacterChunker
from backend.app.ingestion.loaders.factory import get_loader_for_file
from backend.app.schemas.document import IngestionResponse
from backend.app.storage.qdrant_client import QdrantStorageManager

logger = get_logger(__name__)


class IngestionPipeline:
    """Orchestrates document loading, text extraction, chunking, embedding, and persistent indexing."""

    def __init__(
        self,
        storage_manager: QdrantStorageManager,
        embedding_model: BaseEmbeddings,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        documents_dir: Optional[Path] = None,
        collection_name: str = "veriweave_documents",
    ):
        self.storage = storage_manager
        self.embeddings = embedding_model
        self.chunker = RecursiveCharacterChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.documents_dir = documents_dir or Path("./data/documents")
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        # Ensure collection exists
        self.storage.ensure_collection(
            collection_name=self.collection_name,
            vector_size=self.embeddings.dimension,
        )

    def ingest_file_stream(
        self,
        file_stream: BinaryIO,
        filename: str,
        doc_id: Optional[str] = None,
    ) -> IngestionResponse:
        """Save uploaded stream to disk and run full ingestion pipeline."""
        clean_doc_id = doc_id or str(uuid.uuid4())
        safe_filename = Path(filename).name
        target_path = self.documents_dir / f"{clean_doc_id}_{safe_filename}"

        try:
            with target_path.open("wb") as buffer:
                shutil.copyfileobj(file_stream, buffer)
            logger.info(f"Saved uploaded file to: {target_path}")

            return self.ingest_from_path(
                file_path=target_path,
                doc_id=clean_doc_id,
                original_filename=safe_filename,
            )
        except Exception as e:
            if target_path.exists():
                target_path.unlink(missing_ok=True)
            logger.error(f"Failed to ingest file stream '{filename}': {e}")
            raise DocumentIngestionError(f"File ingestion failed: {str(e)}")

    def ingest_from_path(
        self,
        file_path: Path,
        doc_id: Optional[str] = None,
        original_filename: Optional[str] = None,
    ) -> IngestionResponse:
        """Load, chunk, embed, and index a file located at file_path."""
        clean_doc_id = doc_id or str(uuid.uuid4())
        display_name = original_filename or file_path.name
        file_size = file_path.stat().st_size
        file_type = file_path.suffix.lower().replace(".", "") or "txt"

        logger.info(f"Starting ingestion for '{display_name}' (ID: {clean_doc_id}, Size: {file_size} bytes)")

        try:
            # 1. Resolve loader and extract pages
            loader = get_loader_for_file(file_path)
            pages = loader.load(file_path)
            total_pages = len(pages)

            # 2. Chunk text preserving metadata
            chunks = self.chunker.chunk_pages(pages=pages, doc_id=clean_doc_id, filename=display_name)
            if not chunks:
                logger.warning(f"No textual content could be chunked for '{display_name}'")
                return IngestionResponse(
                    doc_id=clean_doc_id,
                    filename=display_name,
                    file_type=file_type,
                    file_size_bytes=file_size,
                    page_count=total_pages,
                    chunk_count=0,
                    status="indexed_empty",
                    message="Document parsed but contained no readable text chunks.",
                )

            # 3. Generate dense vector embeddings
            chunk_texts = [c.text for c in chunks]
            embeddings = self.embeddings.embed_documents(chunk_texts)

            # 4. Upsert into persistent Qdrant vector store
            upserted_count = self.storage.upsert_chunks(
                collection_name=self.collection_name,
                chunks=chunks,
                embeddings=embeddings,
            )

            logger.info(f"Ingestion complete: '{display_name}' -> {upserted_count} chunks indexed")
            return IngestionResponse(
                doc_id=clean_doc_id,
                filename=display_name,
                file_type=file_type,
                file_size_bytes=file_size,
                page_count=total_pages,
                chunk_count=upserted_count,
                status="indexed",
                message="Document successfully extracted, chunked, embedded, and indexed.",
            )
        except Exception as e:
            logger.error(f"Error during ingestion of '{display_name}': {e}")
            raise DocumentIngestionError(f"Error ingesting document '{display_name}': {str(e)}")
