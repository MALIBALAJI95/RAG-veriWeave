"""Pydantic schemas for intelligent multi-path routing."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RouteCategory(str, Enum):
    """Primary routing destinations supported by VeriWeave."""
    VECTOR_DOCUMENT = "vector_document"  # Dense or hybrid retrieval over uploaded documents
    STRUCTURED_SQL = "structured_sql"    # Schema-validated query over document catalog
    WEB_SEARCH = "web_search"            # External information from search provider
    MULTI_SOURCE = "multi_source"        # Compound questions requiring multiple sources


class RoutingMode(str, Enum):
    """User-selectable routing mode or automatic inference."""
    AUTO = "auto"                        # Router autonomously decides best path
    DOCUMENT_ONLY = "document_only"      # Force vector document retrieval
    SQL_ONLY = "sql_only"                # Force structured SQL retrieval
    WEB_ONLY = "web_only"                # Force external web search
    MULTI_SOURCE = "multi_source"        # Force multi-source evidence combination


class RoutingDecision(BaseModel):
    """Validated decision output by the routing classifier."""
    route: RouteCategory = Field(description="Selected route for query fulfillment")
    confidence: float = Field(ge=0.0, le=1.0, description="Routing confidence score")
    reasoning: str = Field(description="Explanatory rationale for route selection")
    classification_method: str = Field(description="'logical_rule', 'semantic_llm', 'user_override', 'fallback'")
    selected_strategy: Optional[str] = Field(
        default="baseline",
        description="Retrieval strategy for vector operations",
    )
    required_sources: List[str] = Field(
        default_factory=list,
        description="List of sources to query: 'vector_document', 'structured_sql', 'web_search'",
    )
    sub_queries: Dict[str, str] = Field(
        default_factory=dict,
        description="Source-specific sub-queries for multi-source execution",
    )
    fallback_triggered: bool = Field(default=False, description="Whether low confidence triggered fallback")
