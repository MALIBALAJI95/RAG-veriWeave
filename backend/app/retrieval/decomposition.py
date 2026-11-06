"""Query decomposition engine splitting compound questions into targeted sub-queries."""

import re
from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.generation.ollama_client import OllamaClient
from backend.app.retrieval.base import BaseRetriever
from backend.app.retrieval.fusion import RRFFusionEngine
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.schemas.chat import MetadataFilter, RetrievedChunk

logger = get_logger(__name__)

DECOMPOSITION_PROMPT_TEMPLATE = """You are an AI assistant specialized in analyzing complex questions.
Decompose the following complex or multi-part user question into 2 or 3 distinct, self-contained sub-questions.
Each sub-question must focus on a single aspect necessary to answer the broader question.

Rules:
1. Output each sub-question on its own line.
2. Do not use numbers, bullet points, or markdown.
3. If the question is simple and cannot be meaningfully broken down, return only the original question.

Original Question: {question}

Sub-Questions (one per line):"""


class QueryDecompositionRetriever(BaseRetriever):
    """Decomposes compound questions into sub-queries, retrieves for each, and aggregates evidence."""

    def __init__(
        self,
        base_retriever: SimilarityRetriever,
        ollama_client: OllamaClient,
        max_subqueries: int = 3,
        rrf_k: int = 60,
    ):
        self.base_retriever = base_retriever
        self.client = ollama_client
        self.max_subqueries = max_subqueries
        self.fusion_engine = RRFFusionEngine(k=rrf_k)
        self.last_subqueries: List[str] = []

    def decompose(self, query: str) -> List[str]:
        """Split a complex question into independent sub-queries."""
        prompt = DECOMPOSITION_PROMPT_TEMPLATE.format(question=query)

        subqueries = []
        try:
            raw_text, _, is_fallback = self.client.generate(
                prompt=prompt,
                system_prompt="You decompose complex user questions into concise atomic sub-queries.",
            )

            if not is_fallback and raw_text:
                lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
                cleaned = [re.sub(r"^\d+[\.\)\-]\s*", "", l).strip() for l in lines]
                valid = [c for c in cleaned if len(c) > 5]
                if valid:
                    subqueries = valid[: self.max_subqueries]
            else:
                subqueries = self._rule_based_decomposition(query)
        except Exception as e:
            logger.warning(f"Decomposition LLM error: {e}. Using rule-based fallback.")
            subqueries = self._rule_based_decomposition(query)

        if not subqueries:
            subqueries = [query]

        self.last_subqueries = subqueries
        logger.info(f"Query decomposed into {len(subqueries)} sub-queries: {subqueries}")
        return subqueries

    def _rule_based_decomposition(self, query: str) -> List[str]:
        """Split query by conjunctions or compound clauses if LLM is offline."""
        q = query.strip()
        # Look for conjunctions: " and ", " as well as ", " versus ", " vs "
        split_patterns = [
            r"\s+and\s+(?:how|what|why|where|when|which)\s+",
            r"\s+as\s+well\s+as\s+",
            r"\s+(?:versus|vs\.?)\s+",
            r"\s+while\s+",
        ]

        for pat in split_patterns:
            parts = re.split(pat, q, flags=re.IGNORECASE)
            if len(parts) > 1:
                sub_qs = []
                for idx, p in enumerate(parts):
                    p_clean = p.strip().rstrip("?")
                    if not p_clean.lower().startswith(("what", "how", "why", "can", "is", "are")):
                        p_clean = f"What is {p_clean}"
                    sub_qs.append(p_clean + "?")
                return sub_qs[: self.max_subqueries]

        return [q]

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
        filters: Optional[MetadataFilter] = None,
    ) -> List[RetrievedChunk]:
        """Retrieve supporting evidence across all sub-queries and fuse with RRF."""
        subqueries = self.decompose(query)

        candidate_lists: List[List[RetrievedChunk]] = []
        labels: List[str] = []

        for idx, sub_q in enumerate(subqueries):
            chunks = self.base_retriever.retrieve(
                query=sub_q,
                top_k=max(top_k, 4),
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
            if chunks:
                candidate_lists.append(chunks)
                labels.append(f"subquery_{idx}")

        if not candidate_lists:
            return []

        fused = self.fusion_engine.fuse(
            ranked_lists=candidate_lists,
            top_k=top_k,
            source_labels=labels,
        )

        for chunk in fused:
            chunk.retrieval_method = "query_decomposition"

        return fused
