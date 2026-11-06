"""Execution handler for vector document retrieval."""

from typing import List, Optional
from backend.app.core.logging import get_logger
from backend.app.retrieval.orchestrator import RetrievalOrchestrator
from backend.app.routing.evidence import EvidenceItem, from_retrieved_chunk
from backend.app.schemas.chat import MetadataFilter
from backend.app.schemas.strategy import RetrievalStrategy

logger = get_logger(__name__)


class VectorRouteHandler:
    """Handles retrieval requests routed to uploaded document vector storage."""

    def __init__(self, orchestrator: RetrievalOrchestrator):
        self.orchestrator = orchestrator
        self.last_metadata = None

    def execute(
        self,
        query: str,
        strategy: RetrievalStrategy = RetrievalStrategy.BASELINE,
        top_k: int = 4,
        score_threshold: Optional[float] = None,
        rerank: bool = False,
        filters: Optional[MetadataFilter] = None,
        doc_id_filter: Optional[str] = None,
    ) -> List[EvidenceItem]:
        """Execute vector retrieval and normalize results into unified EvidenceItems."""
        chunks, meta = self.orchestrator.retrieve(
            query=query,
            strategy=strategy,
            top_k=top_k,
            score_threshold=score_threshold,
            rerank=rerank,
            doc_id_filter=doc_id_filter,
            filters=filters,
        )
        self.last_metadata = meta

        evidence_items = [from_retrieved_chunk(c, idx) for idx, c in enumerate(chunks, 1)]
        logger.info(f"VectorRouteHandler retrieved {len(evidence_items)} evidence chunks for: '{query[:40]}...'")
        return evidence_items
