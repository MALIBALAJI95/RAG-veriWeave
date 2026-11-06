"""Persistent Qdrant vector store management."""

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from qdrant_client.models import Distance, PointStruct, VectorParams
from backend.app.core.exceptions import VectorStorageError
from backend.app.core.logging import get_logger
from backend.app.schemas.chat import RetrievedChunk
from backend.app.schemas.document import DocumentChunk

logger = get_logger(__name__)


class QdrantStorageManager:
    """Manages persistent on-disk Qdrant vector collections and point operations."""

    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing persistent Qdrant client at: {self.storage_path.resolve()}")
        try:
            self.client = QdrantClient(path=str(self.storage_path))
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant at {self.storage_path}: {e}")
            raise VectorStorageError(f"Could not initialize persistent Qdrant storage: {str(e)}")

    def ensure_collection(
        self,
        collection_name: str,
        vector_size: int = 384,
        distance: Distance = Distance.COSINE,
    ) -> None:
        """Create the collection if it does not exist, verifying vector parameters."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            if not exists:
                logger.info(f"Creating Qdrant collection '{collection_name}' (dim={vector_size}, metric={distance})")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance),
                )
            else:
                logger.debug(f"Qdrant collection '{collection_name}' already exists.")
        except Exception as e:
            logger.error(f"Error ensuring collection '{collection_name}': {e}")
            raise VectorStorageError(f"Failed to ensure collection {collection_name}: {str(e)}")

    @staticmethod
    def _to_uuid(key: str) -> str:
        """Deterministically map string ID to valid RFC 4122 UUID for Qdrant point IDs."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))

    def upsert_chunks(
        self,
        collection_name: str,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        """Upsert document chunks and their vector embeddings into persistent Qdrant."""
        if not chunks:
            return 0
        if len(chunks) != len(embeddings):
            raise ValueError(f"Chunk count ({len(chunks)}) does not match embedding count ({len(embeddings)})")

        points: List[PointStruct] = []
        for chunk, emb in zip(chunks, embeddings):
            point_id = self._to_uuid(chunk.chunk_id)
            payload = {
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "filename": chunk.filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "char_start": chunk.char_start,
                "char_end": chunk.char_end,
                "token_count_estimate": chunk.token_count_estimate,
                "metadata": chunk.metadata,
            }
            points.append(PointStruct(id=point_id, vector=emb, payload=payload))

        try:
            # Batch upsert points
            self.client.upsert(collection_name=collection_name, points=points)
            logger.info(f"Successfully upserted {len(points)} chunks into '{collection_name}'")
            return len(points)
        except Exception as e:
            logger.error(f"Failed to upsert points into '{collection_name}': {e}")
            raise VectorStorageError(f"Upsert failed for collection {collection_name}: {str(e)}")

    def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """Perform vector similarity search against the collection."""
        try:
            query_filter = None
            if doc_id_filter:
                query_filter = rest_models.Filter(
                    must=[
                        rest_models.FieldCondition(
                            key="doc_id",
                            match=rest_models.MatchValue(value=doc_id_filter),
                        )
                    ]
                )

            # Support both qdrant-client 1.20+ (query_points) and 1.8-1.19 (search)
            if hasattr(self.client, "query_points"):
                search_response = self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    limit=top_k,
                    score_threshold=score_threshold,
                    query_filter=query_filter,
                    with_payload=True,
                )
                search_results = search_response.points
            else:
                search_results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    score_threshold=score_threshold,
                    query_filter=query_filter,
                    with_payload=True,
                )

            retrieved: List[RetrievedChunk] = []
            for hit in search_results:
                payload = hit.payload or {}
                chunk = RetrievedChunk(
                    chunk_id=payload.get("chunk_id", str(hit.id)),
                    doc_id=payload.get("doc_id", ""),
                    filename=payload.get("filename", "unknown"),
                    page_number=payload.get("page_number", 1),
                    chunk_index=payload.get("chunk_index", 0),
                    text=payload.get("text", ""),
                    score=float(hit.score),
                    metadata=payload.get("metadata", {}),
                )
                retrieved.append(chunk)

            logger.info(f"Retrieved {len(retrieved)} chunks (top_k={top_k}, threshold={score_threshold})")
            return retrieved
        except Exception as e:
            logger.error(f"Similarity search failed in collection '{collection_name}': {e}")
            raise VectorStorageError(f"Vector search failed: {str(e)}")

    def delete_document(self, collection_name: str, doc_id: str) -> int:
        """Delete all points associated with a specific document ID."""
        try:
            filter_selector = rest_models.Filter(
                must=[
                    rest_models.FieldCondition(
                        key="doc_id",
                        match=rest_models.MatchValue(value=doc_id),
                    )
                ]
            )

            # Count points matching filter before deletion
            count_result = self.client.count(
                collection_name=collection_name,
                count_filter=filter_selector,
                exact=True,
            )
            total_points = count_result.count

            if total_points > 0:
                self.client.delete(
                    collection_name=collection_name,
                    points_selector=rest_models.FilterSelector(filter=filter_selector),
                )
                logger.info(f"Deleted {total_points} chunks for doc_id '{doc_id}' from '{collection_name}'")

            return total_points
        except Exception as e:
            logger.error(f"Failed to delete document '{doc_id}': {e}")
            raise VectorStorageError(f"Delete failed for doc_id {doc_id}: {str(e)}")

    def list_documents(self, collection_name: str) -> List[Dict[str, Any]]:
        """List distinct documents and aggregate statistics stored in the collection."""
        try:
            # Scroll through all points in collection
            doc_map: Dict[str, Dict[str, Any]] = {}
            offset = None

            while True:
                records, next_offset = self.client.scroll(
                    collection_name=collection_name,
                    limit=200,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
                for rec in records:
                    payload = rec.payload or {}
                    doc_id = payload.get("doc_id")
                    if not doc_id:
                        continue

                    if doc_id not in doc_map:
                        doc_map[doc_id] = {
                            "doc_id": doc_id,
                            "filename": payload.get("filename", "unknown"),
                            "page_numbers": set(),
                            "chunk_count": 0,
                            "file_type": Path(payload.get("filename", "")).suffix.replace(".", "") or "txt",
                        }

                    doc_map[doc_id]["chunk_count"] += 1
                    doc_map[doc_id]["page_numbers"].add(payload.get("page_number", 1))

                if next_offset is None:
                    break
                offset = next_offset

            # Format documents summary
            results = []
            for doc in doc_map.values():
                results.append(
                    {
                        "doc_id": doc["doc_id"],
                        "filename": doc["filename"],
                        "file_type": doc["file_type"],
                        "page_count": len(doc["page_numbers"]),
                        "chunk_count": doc["chunk_count"],
                    }
                )
            return results
        except Exception as e:
            logger.error(f"Failed to list documents from collection '{collection_name}': {e}")
            raise VectorStorageError(f"Failed to list documents: {str(e)}")

    def get_document_chunks(self, collection_name: str, doc_id: str) -> List[DocumentChunk]:
        """Fetch all chunks for a specific document ordered by chunk_index."""
        try:
            filter_selector = rest_models.Filter(
                must=[
                    rest_models.FieldCondition(
                        key="doc_id",
                        match=rest_models.MatchValue(value=doc_id),
                    )
                ]
            )
            records, _ = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_selector,
                limit=1000,
                with_payload=True,
                with_vectors=False,
            )

            chunks: List[DocumentChunk] = []
            for rec in records:
                p = rec.payload or {}
                chunks.append(
                    DocumentChunk(
                        chunk_id=p.get("chunk_id", str(rec.id)),
                        doc_id=p.get("doc_id", doc_id),
                        filename=p.get("filename", ""),
                        page_number=p.get("page_number", 1),
                        chunk_index=p.get("chunk_index", 0),
                        text=p.get("text", ""),
                        char_start=p.get("char_start", 0),
                        char_end=p.get("char_end", 0),
                        token_count_estimate=p.get("token_count_estimate", 0),
                        metadata=p.get("metadata", {}),
                    )
                )

            chunks.sort(key=lambda c: c.chunk_index)
            return chunks
        except Exception as e:
            logger.error(f"Failed to get chunks for doc_id '{doc_id}': {e}")
            raise VectorStorageError(f"Failed to get document chunks: {str(e)}")

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get collection metrics (total vectors, indexed points, status)."""
        try:
            info = self.client.get_collection(collection_name=collection_name)
            points_count = getattr(info, "points_count", 0) or 0
            vectors_count = (
                getattr(info, "indexed_vectors_count", None)
                or getattr(info, "vectors_count", None)
                or points_count
            )
            return {
                "collection_name": collection_name,
                "status": str(info.status),
                "vectors_count": vectors_count,
                "points_count": points_count,
            }
        except Exception as e:
            logger.warning(f"Could not get info for collection '{collection_name}': {e}")
            return {"collection_name": collection_name, "status": "unknown", "error": str(e)}
