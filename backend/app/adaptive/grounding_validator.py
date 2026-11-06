"""Grounding and hallucination validation engine verifying answer claims and citations."""

import json
import re
from typing import List, Optional, Set
from backend.app.adaptive.schemas import GroundingValidationResult
from backend.app.core.logging import get_logger
from backend.app.generation.ollama_client import OllamaClient
from backend.app.routing.evidence import EvidenceItem
from backend.app.schemas.chat import Citation

logger = get_logger(__name__)

GROUNDING_PROMPT_TEMPLATE = """You are a strict hallucination auditor and citation validator for an enterprise RAG system.
Verify whether the generated answer is strictly grounded in the provided evidence items.

User Question: {question}

Retrieved Evidence Context:
\"\"\"{context}\"\"\"

Generated Answer:
\"\"\"{answer}\"\"\"

Instructions:
1. Verify each factual claim in the answer. List supported claims and unsupported claims.
2. Check that citations refer to genuine evidence.
3. If the answer states that available documents are insufficient, mark it as grounded.
4. Return valid JSON only with this schema:
{{
  "is_grounded": true/false,
  "supported_claims": ["claim 1", "claim 2"],
  "unsupported_claims": ["unsupported claim if any"],
  "citation_valid": true/false,
  "missing_citations": [],
  "reason": "Summary of verification"
}}

JSON Validation:"""


class GroundingValidator:
    """Validates that generated answers are faithful to evidence and free from hallucinations."""

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
    ):
        self.client = ollama_client

    def validate(
        self,
        query: str,
        answer: str,
        evidence_items: List[EvidenceItem],
        citations: List[Citation],
        attempt_number: int = 1,
    ) -> GroundingValidationResult:
        """Evaluate answer faithfulness and citation accuracy."""
        # 1. Attempt LLM-based hallucination detection
        if self.client:
            llm_res = self._validate_llm(query, answer, evidence_items, citations, attempt_number)
            if llm_res is not None:
                return llm_res

        # 2. Deterministic Fallback Validation
        return self._validate_deterministic(query, answer, evidence_items, citations, attempt_number)

    def _validate_llm(
        self,
        query: str,
        answer: str,
        evidence_items: List[EvidenceItem],
        citations: List[Citation],
        attempt_number: int,
    ) -> Optional[GroundingValidationResult]:
        """Query Ollama to perform claim-by-claim verification."""
        try:
            context_blocks = "\n\n".join([
                f"[Source {idx} - {e.source_type} ({e.filename or e.title or e.source_id})]:\n{e.content_excerpt}"
                for idx, e in enumerate(evidence_items, 1)
            ])
            prompt = GROUNDING_PROMPT_TEMPLATE.format(
                question=query,
                context=context_blocks[:2000],
                answer=answer[:1000],
            )
            raw_response, _, is_fallback = self.client.generate(
                prompt=prompt,
                system_prompt="You audit AI responses for hallucinations and citation accuracy. Output JSON only.",
            )
            if is_fallback or not raw_response:
                return None

            json_match = re.search(r"\{.*?\}", raw_response, re.DOTALL)
            if not json_match:
                return None

            data = json.loads(json_match.group(0))
            is_grounded = bool(data.get("is_grounded", True))
            supported = list(data.get("supported_claims", []))
            unsupported = list(data.get("unsupported_claims", []))
            cit_valid = bool(data.get("citation_valid", True))
            missing = list(data.get("missing_citations", []))
            reason = str(data.get("reason", "LLM grounding validation complete."))

            return GroundingValidationResult(
                is_grounded=is_grounded,
                supported_claims=supported,
                unsupported_claims=unsupported,
                citation_valid=cit_valid,
                missing_citations=missing,
                validation_reason=reason,
                attempt_number=attempt_number,
            )
        except Exception as e:
            logger.debug(f"LLM grounding validation failed: {e}")
            return None

    def _validate_deterministic(
        self,
        query: str,
        answer: str,
        evidence_items: List[EvidenceItem],
        citations: List[Citation],
        attempt_number: int,
    ) -> GroundingValidationResult:
        """Deterministic lexical entailment and citation reference verification."""
        # Check if answer is an explicit admission of insufficient evidence
        ans_lower = answer.lower()
        if any(p in ans_lower for p in [
            "do not contain sufficient",
            "not contain sufficient",
            "no relevant documents found",
            "insufficient evidence",
            "cannot be answered based on the provided",
        ]):
            return GroundingValidationResult(
                is_grounded=True,
                supported_claims=["System accurately declared insufficient context."],
                unsupported_claims=[],
                citation_valid=True,
                missing_citations=[],
                validation_reason="Truthful declaration of insufficient evidence without hallucination.",
                attempt_number=attempt_number,
            )

        # 1. Validate Citations
        # Verify that all returned citations map to existing evidence items
        evidence_source_ids = {e.source_id for e in evidence_items}
        evidence_filenames = {e.filename for e in evidence_items if e.filename}
        
        citation_valid = True
        for cit in citations:
            # Check if citation refers to valid source
            if cit.doc_id != "structured_sqlite_db" and cit.doc_id != "external_web_source":
                # For document citations
                if cit.filename not in evidence_filenames and not any(cit.filename in (e.filename or "") for e in evidence_items):
                    citation_valid = False
                    break

        # 2. Check factual claim coverage against evidence
        # Split answer into sentences
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", answer) if len(s.strip()) > 15]
        
        all_evidence_text = " ".join([e.content_excerpt.lower() for e in evidence_items])
        
        supported_claims: List[str] = []
        unsupported_claims: List[str] = []

        for sent in sentences:
            # Filter out introductory / disclaimer sentences
            sent_lower = sent.lower()
            if any(h in sent_lower for h in ["based on the", "here is the", "according to", "start ollama"]):
                continue

            # Extract substantive words (> 3 chars)
            words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]+\b", sent_lower) if len(w) > 3]
            if not words:
                continue

            # Check overlap against evidence corpus
            matches = [w for w in words if w in all_evidence_text]
            overlap_pct = len(matches) / len(words) if words else 1.0

            if overlap_pct >= 0.40:
                supported_claims.append(sent[:120])
            else:
                unsupported_claims.append(sent[:120])

        is_grounded = len(unsupported_claims) == 0 and citation_valid

        reason = (
            f"Deterministic validation: {len(supported_claims)}/{len(supported_claims) + len(unsupported_claims)} claims supported. "
            f"Citations valid: {citation_valid}."
        )

        return GroundingValidationResult(
            is_grounded=is_grounded,
            supported_claims=supported_claims,
            unsupported_claims=unsupported_claims,
            citation_valid=citation_valid,
            missing_citations=[] if citation_valid else ["Unmatched source citation"],
            validation_reason=reason,
            attempt_number=attempt_number,
        )
