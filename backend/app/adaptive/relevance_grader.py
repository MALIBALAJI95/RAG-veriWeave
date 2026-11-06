"""Document and evidence relevance grading with Ollama LLM and deterministic fallback."""

import json
import re
from typing import List, Optional, Set, Tuple
from backend.app.adaptive.schemas import EvidenceRelevanceGrade
from backend.app.core.logging import get_logger
from backend.app.generation.ollama_client import OllamaClient
from backend.app.routing.evidence import EvidenceItem

logger = get_logger(__name__)

STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "could", "did", "do", "does", "doing", "down",
    "during", "each", "few", "for", "from", "further", "had", "has", "have", "having",
    "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i",
    "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most",
    "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
    "or", "other", "our", "ours", "ourselves", "out", "over", "own", "s", "same",
    "she", "should", "so", "some", "such", "t", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with",
    "you", "your", "yours", "yourself", "yourselves",
}

GRADER_PROMPT_TEMPLATE = """You are a strict document relevance grader for an enterprise AI system.
Evaluate whether the following retrieved evidence item contains information relevant to answering the user's question.

User Question: {question}

Retrieved Evidence Excerpt:
\"\"\"{excerpt}\"\"\"

Instructions:
1. Classify the evidence as relevant (`true`) or irrelevant (`false`).
2. Provide a relevance score between 0.0 and 1.0.
3. Provide a brief 1-sentence diagnostic explanation of why it is relevant or irrelevant.
4. Return ONLY valid JSON with this exact schema:
{{"is_relevant": true/false, "score": 0.85, "reason": "Explanation"}}

JSON Assessment:"""


class EvidenceRelevanceGrader:
    """Evaluates retrieved evidence items for semantic relevance against the user's query."""

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        default_threshold: float = 0.5,
    ):
        self.client = ollama_client
        self.default_threshold = default_threshold

    def grade_item(
        self,
        query: str,
        item: EvidenceItem,
        threshold: Optional[float] = None,
    ) -> EvidenceRelevanceGrade:
        """Grade a single evidence item using LLM if available, falling back to deterministic heuristics."""
        thresh = threshold if threshold is not None else self.default_threshold

        # 1. Attempt LLM-based grading
        if self.client:
            grade = self._grade_llm(query, item, thresh)
            if grade is not None:
                return grade

        # 2. Deterministic Fallback Grader
        return self._grade_deterministic(query, item, thresh)

    def grade_evidence(
        self,
        query: str,
        evidence_items: List[EvidenceItem],
        threshold: Optional[float] = None,
    ) -> Tuple[List[EvidenceRelevanceGrade], List[EvidenceItem], List[EvidenceItem]]:
        """Grade all evidence items and partition into relevant and irrelevant lists.

        Returns: (all_grades, relevant_items, irrelevant_items)
        """
        grades: List[EvidenceRelevanceGrade] = []
        relevant: List[EvidenceItem] = []
        irrelevant: List[EvidenceItem] = []

        for item in evidence_items:
            grade = self.grade_item(query, item, threshold)
            grades.append(grade)
            if grade.is_relevant:
                relevant.append(item)
            else:
                irrelevant.append(item)

        logger.info(
            f"EvidenceRelevanceGrader: {len(relevant)}/{len(evidence_items)} relevant "
            f"(query: '{query[:40]}...')"
        )
        return grades, relevant, irrelevant

    def _grade_llm(
        self,
        query: str,
        item: EvidenceItem,
        threshold: float,
    ) -> Optional[EvidenceRelevanceGrade]:
        """Query Ollama LLM to assess evidence relevance."""
        try:
            prompt = GRADER_PROMPT_TEMPLATE.format(
                question=query,
                excerpt=item.content_excerpt[:600],
            )
            raw_response, _, is_fallback = self.client.generate(
                prompt=prompt,
                system_prompt="You are a strict binary evaluator for document relevance. Output JSON only.",
            )
            if is_fallback or not raw_response:
                return None

            # Extract JSON block
            json_match = re.search(r"\{.*?\}", raw_response, re.DOTALL)
            if not json_match:
                return None

            data = json.loads(json_match.group(0))
            is_rel = bool(data.get("is_relevant", False))
            score = float(data.get("score", 0.8 if is_rel else 0.2))
            reason = str(data.get("reason", "LLM graded relevance."))

            # Enforce threshold alignment
            effective_relevant = is_rel and (score >= threshold)

            return EvidenceRelevanceGrade(
                evidence_id=item.evidence_id,
                is_relevant=effective_relevant,
                score=round(max(0.0, min(1.0, score)), 4),
                reason=reason,
                source_type=item.source_type,
                source_id=item.source_id,
            )
        except Exception as e:
            logger.debug(f"LLM relevance grading failed for {item.evidence_id}: {e}")
            return None

    def _grade_deterministic(
        self,
        query: str,
        item: EvidenceItem,
        threshold: float,
    ) -> EvidenceRelevanceGrade:
        """Deterministic lexical keyword and score heuristic for air-gapped/offline execution."""
        # Clean query tokens
        q_tokens = [
            t.lower()
            for t in re.findall(r"\b[a-zA-Z0-9_\-]+\b", query)
            if t.lower() not in STOP_WORDS and len(t) > 1
        ]

        excerpt_lower = item.content_excerpt.lower()
        title_lower = (item.title or "").lower()

        # Handle empty query
        if not q_tokens:
            score = min(1.0, max(0.0, item.score))
            is_rel = score >= threshold
            return EvidenceRelevanceGrade(
                evidence_id=item.evidence_id,
                is_relevant=is_rel,
                score=round(score, 4),
                reason="Default baseline relevance (empty keywords).",
                source_type=item.source_type,
                source_id=item.source_id,
            )

        # Keyword matching
        matched_tokens = [t for t in q_tokens if t in excerpt_lower or t in title_lower]
        overlap_ratio = len(matched_tokens) / len(q_tokens) if q_tokens else 0.0

        # Special handling for structured SQL and exact identifiers
        if item.source_type == "structured_sql":
            # If query asks about counts, documents, or tables and SQL returned rows
            has_sql_intent = any(k in query.lower() for k in ["how many", "count", "list", "total", "document", "file", "page", "size"])
            if has_sql_intent and not item.metadata.get("empty", False):
                overlap_ratio = max(overlap_ratio, 0.85)

        # Combined score: 60% keyword overlap, 40% retrieval score
        norm_item_score = min(1.0, max(0.0, item.score))
        combined_score = (0.60 * overlap_ratio) + (0.40 * norm_item_score)
        combined_score = min(1.0, max(0.0, combined_score))

        is_relevant = combined_score >= threshold

        reason = (
            f"Deterministic evaluation: {len(matched_tokens)}/{len(q_tokens)} query keywords matched "
            f"('{', '.join(matched_tokens[:3])}') with base retrieval score {norm_item_score:.2f}."
            if is_relevant
            else f"Insufficient keyword overlap ({len(matched_tokens)}/{len(q_tokens)} keywords matched)."
        )

        return EvidenceRelevanceGrade(
            evidence_id=item.evidence_id,
            is_relevant=is_relevant,
            score=round(combined_score, 4),
            reason=reason,
            source_type=item.source_type,
            source_id=item.source_id,
        )
