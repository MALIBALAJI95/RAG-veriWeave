"""Intelligent routing package exports."""

from backend.app.routing.schemas import RouteCategory, RoutingDecision, RoutingMode

__all__ = [
    "RouteCategory",
    "RoutingMode",
    "RoutingDecision",
    "EvidenceItem",
    "from_retrieved_chunk",
    "from_sql_result",
    "from_search_result",
    "QueryAnalyzer",
    "QuerySignals",
    "RouteClassifier",
    "RoutingOrchestrator",
]


def __getattr__(name: str):
    if name == "RouteClassifier":
        from backend.app.routing.classifier import RouteClassifier
        return RouteClassifier
    if name == "RoutingOrchestrator":
        from backend.app.routing.orchestrator import RoutingOrchestrator
        return RoutingOrchestrator
    if name in ("EvidenceItem", "from_retrieved_chunk", "from_sql_result", "from_search_result"):
        import backend.app.routing.evidence as ev
        return getattr(ev, name)
    if name in ("QueryAnalyzer", "QuerySignals"):
        import backend.app.routing.query_analyzer as qa
        return getattr(qa, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
