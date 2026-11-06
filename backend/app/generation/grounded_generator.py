"""Grounded response generator orchestrating context formatting, LLM inference, and citation assembly."""

import time
from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.generation.ollama_client import OllamaClient
from backend.app.generation.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, format_context_blocks
from backend.app.schemas.chat import ChatResponse, Citation, RetrievedChunk

logger = get_logger(__name__)


class GroundedAnswerGenerator:
    """Combines retrieved context with structured prompting to generate verified answers with citations."""

    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client

    def generate_grounded_answer(
        self,
        query: str,
        retrieved_chunks: List[RetrievedChunk],
    ) -> ChatResponse:
        """Format context, invoke generation, build structured citations, and measure latency."""
        start_time = time.perf_counter()

        if not retrieved_chunks:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return ChatResponse(
                query=query,
                answer="No relevant documents found to answer this question. Please upload relevant files first.",
                citations=[],
                retrieved_chunks=[],
                model_used=self.client.model,
                latency_ms=round(elapsed_ms, 2),
                grounded=False,
                fallback_used=False,
            )

        # 1. Build prompt context
        context_str = format_context_blocks(retrieved_chunks)
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context_blocks=context_str,
            question=query,
        )

        # 2. Invoke generator (Ollama or fallback)
        raw_answer, model_used, is_fallback = self.client.generate(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
            retrieved_chunks=retrieved_chunks,
        )

        # 3. Build structured citations from retrieved chunks
        citations: List[Citation] = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            snippet = chunk.text.strip().replace("\n", " ")
            if len(snippet) > 180:
                snippet = snippet[:180] + "..."

            citations.append(
                Citation(
                    citation_id=idx,
                    doc_id=chunk.doc_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    score=round(chunk.score, 4),
                    snippet=snippet,
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"Generated answer in {elapsed_ms:.1f}ms using {model_used} "
            f"({len(citations)} citations, fallback={is_fallback})"
        )

        return ChatResponse(
            query=query,
            answer=raw_answer,
            citations=citations,
            retrieved_chunks=retrieved_chunks,
            model_used=model_used,
            latency_ms=round(elapsed_ms, 2),
            grounded=True,
            fallback_used=is_fallback,
        )
