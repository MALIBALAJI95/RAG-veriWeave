"""Intelligent query routing classifier combining logical rules, semantic LLM classification, and fallback logic."""

import json
import re
from typing import Optional
from backend.app.core.logging import get_logger
from backend.app.generation.ollama_client import OllamaClient
from backend.app.routing.query_analyzer import QueryAnalyzer, QuerySignals
from backend.app.routing.schemas import RouteCategory, RoutingDecision, RoutingMode
from backend.app.schemas.strategy import RetrievalStrategy

logger = get_logger(__name__)

SEMANTIC_ROUTING_PROMPT = """You are an intelligent query router for an enterprise AI knowledge platform.
Classify the user's question into exactly ONE of the following 4 categories:

Categories:
1. `vector_document`: Questions asking about technical concepts, document content, summaries, definitions, or specific pages from uploaded PDFs, DOCXs, or text documents.
2. `structured_sql`: Questions asking about document catalog metadata, file counts, file sizes, page counts, upload dates, or listing files in the database.
3. `web_search`: Questions asking for current real-time news, latest 2025/2026 events, external URLs, or information unavailable in static uploaded files.
4. `multi_source`: Complex compound questions explicitly requiring combinations of uploaded document knowledge, database metadata, and external web information.

Rules:
Return ONLY valid JSON with this exact schema:
{{"route": "<category>", "confidence": <float between 0.0 and 1.0>, "reasoning": "<one-sentence explanation>"}}

Question: {question}

JSON Decision:"""


class RouteClassifier:
    """Classifies queries into optimal routing paths using logical heuristics and semantic LLM inference."""

    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        confidence_threshold: float = 0.65,
    ):
        self.analyzer = QueryAnalyzer()
        self.client = ollama_client
        self.confidence_threshold = confidence_threshold

    def classify(
        self,
        query: str,
        routing_mode: RoutingMode = RoutingMode.AUTO,
        selected_strategy: Optional[RetrievalStrategy] = None,
    ) -> RoutingDecision:
        """Route question autonomously or honor explicit routing mode override."""
        cleaned = query.strip()

        # 1. Handle Explicit User Overrides
        if routing_mode == RoutingMode.DOCUMENT_ONLY:
            return RoutingDecision(
                route=RouteCategory.VECTOR_DOCUMENT,
                confidence=1.0,
                reasoning="Explicit user override: document-only vector retrieval requested.",
                classification_method="user_override",
                selected_strategy=selected_strategy or RetrievalStrategy.BASELINE,
                required_sources=["vector_document"],
            )
        elif routing_mode == RoutingMode.SQL_ONLY:
            return RoutingDecision(
                route=RouteCategory.STRUCTURED_SQL,
                confidence=1.0,
                reasoning="Explicit user override: structured SQL catalog retrieval requested.",
                classification_method="user_override",
                required_sources=["structured_sql"],
            )
        elif routing_mode == RoutingMode.WEB_ONLY:
            return RoutingDecision(
                route=RouteCategory.WEB_SEARCH,
                confidence=1.0,
                reasoning="Explicit user override: external web search requested.",
                classification_method="user_override",
                required_sources=["web_search"],
            )
        elif routing_mode == RoutingMode.MULTI_SOURCE:
            return RoutingDecision(
                route=RouteCategory.MULTI_SOURCE,
                confidence=1.0,
                reasoning="Explicit user override: multi-source retrieval requested.",
                classification_method="user_override",
                selected_strategy=selected_strategy or RetrievalStrategy.HYBRID,
                required_sources=["vector_document", "structured_sql", "web_search"],
                sub_queries={
                    "vector_document": cleaned,
                    "structured_sql": cleaned,
                    "web_search": cleaned,
                },
            )

        # 2. Extract Query Signals for Logical Routing
        signals = self.analyzer.analyze(cleaned)

        # 3. High-Precision Logical Heuristics
        logical_decision = self._classify_logical(signals, selected_strategy)
        if logical_decision.confidence >= self.confidence_threshold:
            logger.info(
                f"Logical routing decided: {logical_decision.route.value} "
                f"(confidence={logical_decision.confidence:.2f}) - {logical_decision.reasoning}"
            )
            return logical_decision

        # 4. Semantic LLM Routing for Ambiguous Queries
        if self.client:
            semantic_decision = self._classify_semantic(cleaned, selected_strategy)
            if semantic_decision and semantic_decision.confidence >= self.confidence_threshold:
                logger.info(
                    f"Semantic routing decided: {semantic_decision.route.value} "
                    f"(confidence={semantic_decision.confidence:.2f}) - {semantic_decision.reasoning}"
                )
                return semantic_decision

        # 5. Safe Fallback to Vector Document Retrieval
        logger.warning(
            f"Routing confidence below threshold ({self.confidence_threshold}). "
            f"Executing safe fallback to vector document retrieval."
        )
        return RoutingDecision(
            route=RouteCategory.VECTOR_DOCUMENT,
            confidence=0.50,
            reasoning="Ambiguous question below confidence threshold; safely defaulted to document retrieval.",
            classification_method="confidence_fallback",
            selected_strategy=selected_strategy or RetrievalStrategy.BASELINE,
            required_sources=["vector_document"],
            fallback_triggered=True,
        )

    def _classify_logical(
        self,
        signals: QuerySignals,
        preferred_strategy: Optional[RetrievalStrategy],
    ) -> RoutingDecision:
        """Evaluate deterministic rules based on lexical and structural query signals."""
        q_lower = signals.cleaned_query.lower()

        # Multi-Source Compound Queries
        if signals.has_multi_source_indicators:
            return RoutingDecision(
                route=RouteCategory.MULTI_SOURCE,
                confidence=0.92,
                reasoning="Query combines uploaded document queries with catalog metadata or external web searches.",
                classification_method="logical_rule",
                selected_strategy=preferred_strategy or RetrievalStrategy.HYBRID,
                required_sources=["vector_document", "structured_sql", "web_search"],
                sub_queries={
                    "vector_document": signals.cleaned_query,
                    "structured_sql": signals.cleaned_query,
                    "web_search": signals.cleaned_query,
                },
            )

        # Structured Database Queries
        if signals.has_sql_keywords and not signals.has_web_keywords:
            return RoutingDecision(
                route=RouteCategory.STRUCTURED_SQL,
                confidence=0.95,
                reasoning="Query requests structured metadata, document counts, file types, or catalog aggregation.",
                classification_method="logical_rule",
                required_sources=["structured_sql"],
            )

        # External Web Search Queries
        if signals.has_web_keywords and not any(k in q_lower for k in ["pdf", "docx", "our doc", "uploaded", "page"]):
            return RoutingDecision(
                route=RouteCategory.WEB_SEARCH,
                confidence=0.90,
                reasoning="Query references current news, external releases, or events outside static uploaded documents.",
                classification_method="logical_rule",
                required_sources=["web_search"],
            )

        # Exact Keyword / Acronym Document Retrieval -> Hybrid or Baseline Strategy
        if signals.has_exact_identifiers:
            chosen_strat = preferred_strategy or RetrievalStrategy.HYBRID
            return RoutingDecision(
                route=RouteCategory.VECTOR_DOCUMENT,
                confidence=0.92,
                reasoning="Query contains technical identifiers, exact terms, or acronyms suitable for hybrid document retrieval.",
                classification_method="logical_rule",
                selected_strategy=chosen_strat,
                required_sources=["vector_document"],
            )

        # Document Semantic Questions (RAG, agent concepts, definitions)
        if any(w in q_lower for w in ["what", "how", "why", "explain", "describe", "architecture", "rag", "agent", "memory", "retrieval", "page"]):
            return RoutingDecision(
                route=RouteCategory.VECTOR_DOCUMENT,
                confidence=0.88,
                reasoning="Query asks for explanatory or factual content residing in uploaded reference documents.",
                classification_method="logical_rule",
                selected_strategy=preferred_strategy or RetrievalStrategy.BASELINE,
                required_sources=["vector_document"],
            )

        # Ambiguous
        return RoutingDecision(
            route=RouteCategory.VECTOR_DOCUMENT,
            confidence=0.45,
            reasoning="Query lacks definitive signals for deterministic routing.",
            classification_method="logical_rule",
            selected_strategy=preferred_strategy or RetrievalStrategy.BASELINE,
            required_sources=["vector_document"],
        )

    def _classify_semantic(
        self,
        query: str,
        preferred_strategy: Optional[RetrievalStrategy],
    ) -> Optional[RoutingDecision]:
        """Query local Ollama model to classify ambiguous questions."""
        if not self.client:
            return None

        prompt = SEMANTIC_ROUTING_PROMPT.format(question=query)
        try:
            raw_output, _, is_fallback = self.client.generate(
                prompt=prompt,
                system_prompt="You are a strict JSON classifier. Output only valid JSON without markdown formatting.",
            )
            if is_fallback or not raw_output:
                return None

            cleaned_json = re.sub(r"^```(?:json)?", "", raw_output.strip())
            cleaned_json = re.sub(r"```$", "", cleaned_json).strip()

            data = json.loads(cleaned_json)
            raw_route = str(data.get("route", "")).strip().lower()
            confidence = float(data.get("confidence", 0.7))
            reasoning = str(data.get("reasoning", "Semantic LLM classification"))

            if raw_route in [r.value for r in RouteCategory]:
                category = RouteCategory(raw_route)
                sources = [category.value]
                sub_queries = {}
                if category == RouteCategory.MULTI_SOURCE:
                    sources = ["vector_document", "structured_sql", "web_search"]
                    sub_queries = {s: query for s in sources}

                return RoutingDecision(
                    route=category,
                    confidence=min(1.0, max(0.0, confidence)),
                    reasoning=f"LLM Classification: {reasoning}",
                    classification_method="semantic_llm",
                    selected_strategy=preferred_strategy or RetrievalStrategy.BASELINE,
                    required_sources=sources,
                    sub_queries=sub_queries,
                )
        except Exception as e:
            logger.debug(f"Semantic LLM routing parse failed: {e}")

        return None
