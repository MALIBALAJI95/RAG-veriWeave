"""Multi-Query retrieval engine generating diverse linguistic perspectives of the query."""

import re
from typing import List, Optional, Tuple
from backend.app.core.logging import get_logger
from backend.app.generation.ollama_client import OllamaClient
from backend.app.retrieval.base import BaseRetriever
from backend.app.retrieval.fusion import RRFFusionEngine
from backend.app.retrieval.similarity_retriever import SimilarityRetriever
from backend.app.schemas.chat import MetadataFilter, RetrievedChunk

logger = get_logger(__name__)

MULTI_QUERY_PROMPT_TEMPLATE = """You are an AI assistant specialized in retrieval-augmented generation.
Your task is to generate {num_queries} different natural language versions of the user's input question.
The goal is to capture different perspectives, synonyms, and phrasing to retrieve comprehensive documents from a vector store.

Rules:
1. Provide each alternate question on a separate line.
2. Do not number the questions or add markdown bullet points.
3. Keep the semantic meaning aligned with the original question.

Original Question: {question}

Alternative Queries (one per line):"""


class MultiQueryRetriever(BaseRetriever):
    """Generates multiple query variants using LLM, retrieves for each, and fuses candidates."""

    def __init__(
        self,
        base_retriever: SimilarityRetriever,
        ollama_client: OllamaClient,
        num_queries: int = 3,
        rrf_k: int = 60,
    ):
        self.base_retriever = base_retriever
        self.client = ollama_client
        self.num_queries = num_queries
        self.fusion_engine = RRFFusionEngine(k=rrf_k)
        self.last_generated_queries: List[str] = []

    def generate_queries(self, original_query: str) -> List[str]:
        """Generate alternative query formulations via LLM or rule-based fallback."""
        prompt = MULTI_QUERY_PROMPT_TEMPLATE.format(
            num_queries=self.num_queries,
            question=original_query,
        )

        queries = [original_query]

        try:
            raw_response, _, is_fallback = self.client.generate(
                prompt=prompt,
                system_prompt="You generate diverse search query reformulations without conversational filler.",
            )

            if not is_fallback and raw_response:
                lines = [line.strip() for line in raw_response.split("\n") if line.strip()]
                # Clean numbered prefixes e.g. "1. Query" -> "Query"
                cleaned = [re.sub(r"^\d+[\.\)\-]\s*", "", line).strip() for line in lines]
                valid_lines = [c for c in cleaned if c and len(c) > 5 and c.lower() != original_query.lower()]
                queries.extend(valid_lines[: self.num_queries])
            else:
                # Rule-based syntactic fallback when LLM is offline
                queries.extend(self._synthesize_fallback_queries(original_query))
        except Exception as e:
            logger.warning(f"Multi-query generation error: {e}. Using deterministic query variants.")
            queries.extend(self._synthesize_fallback_queries(original_query))

        # Deduplicate while preserving order
        unique_queries = list(dict.fromkeys(queries))
        self.last_generated_queries = unique_queries
        logger.info(f"Multi-Query generated {len(unique_queries)} queries: {unique_queries}")
        return unique_queries

    def _synthesize_fallback_queries(self, query: str) -> List[str]:
        """Synthesize deterministic semantic variants if Ollama is unreachable."""
        q = query.strip().rstrip("?").lower()
        variants = []
        if q.startswith("what is") or q.startswith("what are"):
            core = re.sub(r"^what (is|are)\s*", "", q)
            variants.append(f"Explain {core} and architectural specifications")
            variants.append(f"Key concepts and definitions of {core}")
        elif q.startswith("how do") or q.startswith("how does"):
            core = re.sub(r"^how (do|does)\s*", "", q)
            variants.append(f"Mechanism and process behind {core}")
            variants.append(f"Implementation details and trade-offs of {core}")
        else:
            variants.append(f"Overview and core components of {q}")
            variants.append(f"Detailed analysis regarding {q}")

        return variants[: self.num_queries]

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        doc_id_filter: Optional[str] = None,
        filters: Optional[MetadataFilter] = None,
    ) -> List[RetrievedChunk]:
        """Execute multi-query expansion, retrieve for all variants, and fuse candidates with RRF."""
        queries = self.generate_queries(query)

        # Retrieve candidates for every query
        candidate_lists: List[List[RetrievedChunk]] = []
        source_labels: List[str] = []

        for idx, sub_q in enumerate(queries):
            chunks = self.base_retriever.retrieve(
                query=sub_q,
                top_k=max(top_k, 5),
                score_threshold=score_threshold,
                doc_id_filter=doc_id_filter,
                filters=filters,
            )
            if chunks:
                candidate_lists.append(chunks)
                source_labels.append(f"query_{idx}")

        if not candidate_lists:
            return []

        # Fuse via RRF
        fused = self.fusion_engine.fuse(
            ranked_lists=candidate_lists,
            top_k=top_k,
            source_labels=source_labels,
        )

        for chunk in fused:
            chunk.retrieval_method = "multi_query_fusion"

        return fused
