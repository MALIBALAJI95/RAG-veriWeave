"""Unified evidence schema and normalizer across vector, SQL, and web sources."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.chat import Citation, RetrievedChunk
from backend.app.web_search.base import SearchResult


class EvidenceItem(BaseModel):
    """Unified cross-source evidence representation."""
    evidence_id: str = Field(description="Unique deterministic evidence identifier")
    source_type: str = Field(description="Origin category: 'vector_document', 'structured_sql', 'web_search'")
    source_id: str = Field(description="Source-specific identifier (e.g. chunk_id, sql_query, url)")
    doc_id: Optional[str] = Field(default=None, description="Document UUID if applicable")
    filename: Optional[str] = Field(default=None, description="Document filename if applicable")
    page_number: Optional[int] = Field(default=None, description="Page number if applicable")
    chunk_index: Optional[int] = Field(default=None, description="Chunk index if applicable")
    record_id: Optional[str] = Field(default=None, description="Database record ID if applicable")
    url: Optional[str] = Field(default=None, description="External URL if applicable")
    title: Optional[str] = Field(default=None, description="Title of document or web article")
    content_excerpt: str = Field(description="Core text evidence")
    score: float = Field(default=1.0, description="Confidence or relevance score")
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_citation(self, citation_id: int) -> Citation:
        """Convert evidence item into user-facing Citation schema preserving exact provenance."""
        # For vector document chunks
        if self.source_type == "vector_document" and self.doc_id:
            return Citation(
                citation_id=citation_id,
                doc_id=self.doc_id,
                filename=self.filename or "unknown",
                page_number=self.page_number or 1,
                chunk_index=self.chunk_index or 0,
                score=round(self.score, 4),
                snippet=self.content_excerpt[:180] + ("..." if len(self.content_excerpt) > 180 else ""),
            )

        # For structured database records
        if self.source_type == "structured_sql":
            return Citation(
                citation_id=citation_id,
                doc_id="structured_sqlite_db",
                filename="Database: SQLite Catalog",
                page_number=1,
                chunk_index=0,
                score=round(self.score, 4),
                snippet=f"[SQL Record] {self.content_excerpt[:160]}",
            )

        # For external web search
        return Citation(
            citation_id=citation_id,
            doc_id="external_web_source",
            filename=f"Web: {self.title or self.url or 'External Source'}",
            page_number=1,
            chunk_index=0,
            score=round(self.score, 4),
            snippet=f"[Web URL: {self.url}] {self.content_excerpt[:160]}",
        )


def from_retrieved_chunk(chunk: RetrievedChunk, idx: int) -> EvidenceItem:
    """Normalize a vector document chunk to EvidenceItem."""
    return EvidenceItem(
        evidence_id=f"ev_vec_{chunk.chunk_id}",
        source_type="vector_document",
        source_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        filename=chunk.filename,
        page_number=chunk.page_number,
        chunk_index=chunk.chunk_index,
        title=chunk.filename,
        content_excerpt=chunk.text,
        score=chunk.score,
        metadata={
            **chunk.metadata,
            "original_rank": chunk.original_rank,
            "retrieval_method": chunk.retrieval_method,
            "rerank_score": chunk.rerank_score,
        },
    )


def from_sql_result(query_executed: str, rows: List[Dict[str, Any]], latency_ms: float) -> List[EvidenceItem]:
    """Normalize structured SQL query rows into EvidenceItems."""
    if not rows:
        return [
            EvidenceItem(
                evidence_id="ev_sql_empty",
                source_type="structured_sql",
                source_id=query_executed,
                content_excerpt=f"Query '{query_executed}' executed successfully but returned 0 rows.",
                score=0.9,
                metadata={"sql_query": query_executed, "latency_ms": latency_ms, "empty": True},
            )
        ]

    items: List[EvidenceItem] = []
    # If single aggregate row e.g. COUNT(*), AVG
    if len(rows) == 1 and any("count" in k.lower() or "avg" in k.lower() or "sum" in k.lower() for k in rows[0].keys()):
        row_str = ", ".join(f"{k} = {v}" for k, v in rows[0].items())
        items.append(
            EvidenceItem(
                evidence_id="ev_sql_agg_0",
                source_type="structured_sql",
                source_id=query_executed,
                content_excerpt=f"Database aggregation result: {row_str}",
                score=1.0,
                metadata={"sql_query": query_executed, "latency_ms": latency_ms},
            )
        )
        return items

    for idx, row in enumerate(rows):
        row_str = " | ".join(f"{k}: {v}" for k, v in row.items())
        doc_id = row.get("doc_id")
        filename = row.get("filename")
        page_num = row.get("page_count") or row.get("page_number")
        items.append(
            EvidenceItem(
                evidence_id=f"ev_sql_row_{idx}",
                source_type="structured_sql",
                source_id=query_executed,
                doc_id=str(doc_id) if doc_id else None,
                filename=str(filename) if filename else None,
                page_number=int(page_num) if page_num and str(page_num).isdigit() else None,
                record_id=str(row.get("id", idx)),
                content_excerpt=f"Catalog record: {row_str}",
                score=0.95,
                metadata={"sql_query": query_executed, "row_data": row},
            )
        )
    return items


def from_search_result(res: SearchResult, idx: int) -> EvidenceItem:
    """Normalize external web search result into EvidenceItem."""
    return EvidenceItem(
        evidence_id=f"ev_web_{idx}",
        source_type="web_search",
        source_id=res.url,
        url=res.url,
        title=res.title,
        content_excerpt=res.snippet,
        score=res.score,
        metadata={**res.metadata, "published_date": res.published_date},
    )
