"""Hypothetical Document Embeddings (HyDE) retrieval engine."""

from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.embeddings.base import BaseEmbeddings
from backend.app.generation.ollama_client import OllamaClient
from backend.app.retrieval.base import BaseRetriever
from backend.app.schemas.chat import MetadataFilter, RetrievedChunk
from backend.app.storage.qdrant_client import QdrantStorageManager

logger = get_logger(__name__)

HYDE_PROMPT_TEMPLATE = """You are an AI generating hypothetical reference documents for dense retrieval.
Please write a short, detailed, factual paragraph that directly answers the question below.
Do not include conversational introductions (e.g. "Sure, here is..."). Write only the explanatory text as if it appeared in a reference manual.

Question: {question}

Hypothetical Reference Passage:"""


class HyDERetriever(BaseRetriever):
    """Retrieves document chunks by embedding a synthesized hypothetical document instead of the raw query."""

    def __init__(
        self,
        storage_manager: QdrantStorageManager,
        embedding_model: BaseEmbeddings,
        ollama_client: OllamaClient,
        collection_name: str = "veriweave_documents",
    ):
        self.storage = storage_manager
        self.embeddings = embedding_model
        self.client = ollama_client
        self.collection_name = collection_name
        self.last_hypothetical_document: Optional[str] = None

    def generate_hypothetical_passage(self, query: str) -> str:
        """Synthesize a hypothetical reference passage for the query."""
        prompt = HYDE_PROMPT_TEMPLATE.format(question=query)

        try:
            raw_text, _, is_fallback = self.client.generate(
                prompt=prompt,
                system_prompt="You generate clear, concise hypothetical reference documents for search queries.",
            )
            if not is_fallback and raw_text and len(raw_text.strip()) > 20:
                hypothetical = raw_text.strip()
            else:
                # Deterministic fallback passage if LLM is offline
                hypothetical = (
                    f"This document provides a technical explanation regarding {query}. "
                    f"It details the architecture, foundational principles, specifications, "
                    f"and operational mechanisms relevant to {query}."
                )
        except Exception as e:
            logger.warning(f"HyDE generation failed ({e}). Using rule-based fallback passage.")
            hypothetical = f"Technical specifications and reference implementation for: {query}"

        self.last_hypothetical_document = hypothetical
        logger.info(f"HyDE generated passage: '{hypothetical[:80]}...'")
        return hypothetical

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
        filters: Optional[MetadataFilter] = None,
    ) -> List[RetrievedChunk]:
        """Generate hypothetical passage, embed it, and retrieve real chunks from Qdrant."""
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        # 1. Generate hypothetical answer text
        hypo_text = self.generate_hypothetical_passage(cleaned_query)

        # 2. Embed the hypothetical document
        hypo_vector = self.embeddings.embed_query(hypo_text)

        # 3. Retrieve actual chunks matching the hypothetical vector
        effective_doc_id = (filters.doc_id if filters else None) or doc_id_filter
        filename_filter = filters.filename if filters else None
        page_number_filter = filters.page_number if filters else None
        custom_filter = filters.custom if filters else None

        results = self.storage.search_similar(
            collection_name=self.collection_name,
            query_vector=hypo_vector,
            top_k=top_k,
            score_threshold=score_threshold,
            doc_id_filter=effective_doc_id,
            filename_filter=filename_filter,
            page_number_filter=page_number_filter,
            custom_filter=custom_filter,
        )

        for rank, chunk in enumerate(results, 1):
            chunk.original_rank = rank
            chunk.retrieval_method = "hyde"
            chunk.metadata = {
                **chunk.metadata,
                "hyde_generated_query_used": True,
            }

        logger.info(f"HyDE retrieved {len(results)} chunks for query: '{cleaned_query[:50]}'")
        return results
