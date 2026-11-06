"""Adaptive query rewriter optimizing search queries when evidence is insufficient."""

import json
import re
from typing import Optional
from backend.app.adaptive.schemas import QueryRewriteResult
from backend.app.core.logging import get_logger
from backend.app.generation.ollama_client import OllamaClient

logger = get_logger(__name__)

CONVERSATIONAL_FILLERS = [
    r"^can you please (?:tell me|explain|describe)\b",
    r"^can you (?:tell me|explain|describe|show me)\b",
    r"^please (?:tell me|explain|describe|show me|provide)\b",
    r"^could you (?:tell me|explain|describe|clarify)\b",
    r"^i would like to know\b",
    r"^i want to understand\b",
    r"^what can you tell me about\b",
    r"^tell me about\b",
    r"^give me information on\b",
    r"^explain to me\b",
]

REWRITE_PROMPT_TEMPLATE = """You are an expert search query reformulator for an enterprise RAG system.
The following user query failed to retrieve sufficient relevant evidence.
Rewrite the query to improve retrieval recall, semantic precision, and search engine relevance.

Rules:
1. Preserve the user's exact informational intent.
2. Do NOT invent new facts, hypothetical entities, or unsupported assumptions.
3. Remove conversational filler phrases and emphasize key technical concepts.
4. Output valid JSON only with this schema:
{{"rewritten_query": "Optimized query here", "reason": "Explanation of change"}}

Original Query: {original_query}
Attempt Number: {attempt_number}
Retrieval Issue: {failure_reason}

JSON Reformulation:"""


class AdaptiveQueryRewriter:
    """Reformulates queries to overcome vocabulary mismatch or insufficient retrieval evidence."""

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        max_rewrites: int = 2,
    ):
        self.client = ollama_client
        self.max_rewrites = max_rewrites

    def rewrite(
        self,
        original_query: str,
        attempt_number: int = 1,
        failure_reason: Optional[str] = None,
    ) -> QueryRewriteResult:
        """Rewrite query using LLM if available, falling back to deterministic heuristic reformulation."""
        issue = failure_reason or "Retrieved evidence had insufficient relevance or zero matching chunks."

        # 1. Attempt LLM-based query rewrite
        if self.client:
            llm_result = self._rewrite_llm(original_query, attempt_number, issue)
            if llm_result:
                logger.info(
                    f"AdaptiveQueryRewriter (LLM Attempt {attempt_number}): "
                    f"'{original_query}' -> '{llm_result.rewritten_query}' ({llm_result.rewrite_reason})"
                )
                return llm_result

        # 2. Deterministic Fallback Rewrite
        fallback_result = self._rewrite_deterministic(original_query, attempt_number, issue)
        logger.info(
            f"AdaptiveQueryRewriter (Fallback Attempt {attempt_number}): "
            f"'{original_query}' -> '{fallback_result.rewritten_query}' ({fallback_result.rewrite_reason})"
        )
        return fallback_result

    def _rewrite_llm(
        self,
        original_query: str,
        attempt_number: int,
        failure_reason: str,
    ) -> Optional[QueryRewriteResult]:
        """Use Ollama to generate a semantically improved query."""
        try:
            prompt = REWRITE_PROMPT_TEMPLATE.format(
                original_query=original_query,
                attempt_number=attempt_number,
                failure_reason=failure_reason,
            )
            raw_response, _, is_fallback = self.client.generate(
                prompt=prompt,
                system_prompt="You reformulate search queries for optimal retrieval precision. Output JSON only.",
            )
            if is_fallback or not raw_response:
                return None

            json_match = re.search(r"\{.*?\}", raw_response, re.DOTALL)
            if not json_match:
                return None

            data = json.loads(json_match.group(0))
            rewritten = data.get("rewritten_query", "").strip()
            reason = data.get("reason", "LLM reformulated query for semantic clarity.")

            if rewritten and rewritten.lower() != original_query.lower():
                return QueryRewriteResult(
                    original_query=original_query,
                    rewritten_query=rewritten,
                    rewrite_reason=reason,
                    attempt_number=attempt_number,
                )
            return None
        except Exception as e:
            logger.debug(f"LLM query rewrite failed: {e}")
            return None

    def _rewrite_deterministic(
        self,
        original_query: str,
        attempt_number: int,
        failure_reason: str,
    ) -> QueryRewriteResult:
        """Deterministic query reformulation: removes conversational noise, restructures syntax."""
        cleaned = original_query.strip()
        q_lower = cleaned.lower()

        # Step 1: Strip conversational filler
        rewritten = cleaned
        for pat in CONVERSATIONAL_FILLERS:
            rewritten = re.sub(pat, "", rewritten, flags=re.IGNORECASE).strip()

        # Remove leading punctuation or question marks
        rewritten = re.sub(r"^[?,.:;\s]+", "", rewritten).strip()
        rewritten = re.sub(r"[?]+$", "", rewritten).strip()

        # Step 2: Attempt-specific reformulation
        if attempt_number == 1:
            # If query stripped to empty or unchanged, expand key nouns
            if not rewritten or rewritten.lower() == original_query.lower():
                # Add domain search context
                rewritten = f"{cleaned} architecture methodology details"
                reason = "Removed conversational framing and focused query on core subject keywords."
            else:
                reason = "Stripped conversational prefix to isolate core search entities."
        else:
            # Attempt 2+: Extract key nouns and acronyms
            words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]+\b", cleaned) if len(w) > 2]
            if len(words) >= 2:
                rewritten = " ".join(words)
                reason = f"Keyword extraction pass (attempt {attempt_number}) targeting dense lexical overlap."
            else:
                rewritten = f"{cleaned} concepts principles overview"
                reason = f"Broadened query terms for second retrieval cycle (attempt {attempt_number})."

        return QueryRewriteResult(
            original_query=original_query,
            rewritten_query=rewritten,
            rewrite_reason=reason,
            attempt_number=attempt_number,
        )
