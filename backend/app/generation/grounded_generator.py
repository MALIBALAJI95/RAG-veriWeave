"""Grounded response generator orchestrating context formatting, LLM inference, and multi-source citations."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, List, Optional
from backend.app.core.logging import get_logger
from backend.app.generation.ollama_client import OllamaClient
from backend.app.generation.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, format_context_blocks

if TYPE_CHECKING:
    from backend.app.schemas.chat import ChatResponse, Citation, RetrievedChunk

logger = get_logger(__name__)


class GroundedAnswerGenerator:
    """Combines retrieved context with structured prompting to generate verified answers with citations."""

    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client

    def generate_grounded_answer(
        self,
        query: str,
        retrieved_chunks: List[Any],
        retrieval_metadata: Optional[Any] = None,
        evidence_items: Optional[List[Any]] = None,
    ) -> ChatResponse:
        """Format context, invoke generation, build structured citations, and measure latency."""
        from backend.app.schemas.chat import ChatResponse, Citation, RetrievedChunk
        start_time = time.perf_counter()
        context_items = evidence_items if evidence_items is not None else retrieved_chunks

        if not context_items:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ChatResponse(
                query=query,
                answer="No relevant documents found to answer this question. Please upload relevant files or verify query parameters.",
                citations=[],
                retrieved_chunks=retrieved_chunks if all(isinstance(x, RetrievedChunk) for x in retrieved_chunks) else [],
                model_used=self.client.model,
                latency_ms=round(elapsed_ms, 2),
                grounded=False,
                fallback_used=False,
                retrieval_metadata=retrieval_metadata,
            )

        # 1. Build prompt context with origin provenance
        context_str = format_context_blocks(context_items)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context_blocks=context_str,
            question=query,
        )

        # 2. Invoke generator (Ollama or fallback)
        raw_answer, model_used, is_fallback = self.client.generate(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            retrieved_chunks=retrieved_chunks if all(isinstance(x, RetrievedChunk) for x in retrieved_chunks) else None,
        )

        # 3. Build structured citations accurately from items
        citations: List[Citation] = []
        chunks_for_response: List[RetrievedChunk] = []

        for idx, item in enumerate(context_items, 1):
            if hasattr(item, "to_citation"):
                citations.append(item.to_citation(citation_id=idx))
            else:
                snippet = item.text.strip().replace("\n", " ")
                if len(snippet) > 180:
                    snippet = snippet[:180] + "..."
                citations.append(
                    Citation(
                        citation_id=idx,
                        doc_id=item.doc_id,
                        filename=item.filename,
                        page_number=item.page_number,
                        chunk_index=item.chunk_index,
                        score=round(item.score, 4),
                        snippet=snippet,
                    )
                )

            if isinstance(item, RetrievedChunk):
                chunks_for_response.append(item)
            elif hasattr(item, "source_type") and item.source_type == "vector_document":
                # Convert EvidenceItem back to RetrievedChunk representation for response
                chunks_for_response.append(
                    RetrievedChunk(
                        chunk_id=item.source_id,
                        doc_id=item.doc_id or "doc",
                        filename=item.filename or "unknown",
                        page_number=item.page_number or 1,
                        chunk_index=item.chunk_index or 0,
                        text=item.content_excerpt,
                        score=item.score,
                        metadata=item.metadata,
                    )
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Generated grounded answer in {elapsed_ms:.1f}ms using {model_used} "
            f"({len(citations)} citations, fallback={is_fallback})"
        )

        return ChatResponse(
            query=query,
            answer=raw_answer,
            citations=citations,
            retrieved_chunks=chunks_for_response,
            model_used=model_used,
            latency_ms=round(elapsed_ms, 2),
            grounded=True,
            fallback_used=is_fallback,
            retrieval_metadata=retrieval_metadata,
        )
