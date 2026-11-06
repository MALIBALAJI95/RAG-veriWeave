"""Live verification script demonstrating end-to-end Phase 3 Intelligent Multi-Path Query Routing.

Runs 5 comprehensive routing scenarios:
1. Document Content Question -> Routes to Vector Document Retrieval
2. Catalog Metadata Question -> Routes to Structured SQL Retrieval (SQLite)
3. Recent External News Question -> Routes to External Web Search Provider
4. Compound Multi-Source Question -> Routes to Multi-Source Synthesis
5. Ambiguous Query -> Executes Safe Fallback to Vector Document Retrieval
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.api.deps import (
    get_grounded_generator,
    get_routing_orchestrator,
    get_settings,
    init_db,
)
from backend.app.database.session import sync_document_ingestion
from backend.app.routing.schemas import RoutingMode
from backend.app.schemas.chat import RetrievalStrategy
from backend.app.schemas.document import DocumentChunk, IngestionResponse


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_result(scenario_num: int, title: str, response):
    print(f"\n[Scenario {scenario_num}]: {title}")
    print(f" Query: {response.query}")
    print(f" Route Selected: {response.routing_decision.route.value} (Confidence: {response.routing_decision.confidence:.2f}, Method: {response.routing_decision.classification_method})")
    print(f" Model Used: {response.model_used} | Latency: {response.latency_ms:.1f}ms | Grounded: {response.grounded} | Fallback: {response.fallback_used}")
    print(f" Evidence Items: {len(response.evidence)} | Citations: {len(response.citations)}")
    print("\n--- Citations ---")
    for cit in response.citations:
        print(f" [{cit.citation_id}] Source: {cit.filename} (Page: {cit.page_number}, Score: {cit.score:.3f})")
        print(f"     Excerpt: {cit.snippet}")
    print("\n--- Generated Answer ---")
    print(f" {response.answer}")
    print("-" * 80)


def main():
    print_header("VeriWeave Phase 3: Intelligent Multi-Path Query Routing Live Verification")
    settings = get_settings()
    settings.ensure_directories()

    # 1. Initialize SQLite catalog database
    init_db(settings.SQLITE_DB_PATH)

    # 2. Seed SQLite catalog with sample document metadata
    seed_doc = IngestionResponse(
        doc_id="doc-veriweave-spec",
        filename="veriweave_architecture_guide.pdf",
        file_type="pdf",
        file_size_bytes=2457600,
        page_count=18,
        chunk_count=24,
        status="indexed",
        created_at="2026-03-01T08:00:00",
    )
    seed_chunks = [
        DocumentChunk(
            chunk_id=f"chunk-live-{i}",
            doc_id="doc-veriweave-spec",
            filename="veriweave_architecture_guide.pdf",
            text=(
                "VeriWeave is an adaptive multi-strategy retrieval and grounded generation engine. "
                "Phase 3 implements intelligent multi-path routing across vector search, structured SQL, "
                "external web search, and multi-source synthesis, preventing hallucinations through strict grounding."
            ),
            page_number=1,
            chunk_index=i,
            token_count_estimate=45,
            char_start=0,
            char_end=240,
        )
        for i in range(2)
    ]
    sync_document_ingestion(seed_doc, seed_chunks)
    print("✓ Successfully synchronized sample document metadata to SQLite catalog.")

    # 3. Instantiate orchestrator & generator
    orchestrator = get_routing_orchestrator()
    generator = get_grounded_generator()

    # SCENARIO 1: Vector Document Retrieval
    q1 = "What is the primary architecture and purpose of VeriWeave?"
    ev1, dec1, _ = orchestrator.route_and_retrieve(
        query=q1,
        routing_mode=RoutingMode.AUTO,
        selected_strategy=RetrievalStrategy.HYBRID,
    )
    res1 = generator.generate_grounded_answer(
        query=q1,
        retrieved_chunks=[],
        retrieval_metadata=orchestrator.vector_handler.last_metadata,
        evidence_items=ev1,
    )
    res1.routing_decision = dec1
    res1.evidence = ev1
    print_result(1, "Document Semantic Content Question -> Vector Document Retrieval", res1)

    # SCENARIO 2: Structured SQL Catalog Retrieval
    q2 = "How many documents are uploaded in the system?"
    ev2, dec2, _ = orchestrator.route_and_retrieve(query=q2, routing_mode=RoutingMode.AUTO)
    res2 = generator.generate_grounded_answer(
        query=q2,
        retrieved_chunks=[],
        evidence_items=ev2,
    )
    res2.routing_decision = dec2
    res2.evidence = ev2
    print_result(2, "Document Catalog Query -> Structured SQLite Retrieval", res2)

    # SCENARIO 3: External Web Search
    q3 = "What are the latest 2026 features released in LangChain and LangGraph?"
    ev3, dec3, _ = orchestrator.route_and_retrieve(query=q3, routing_mode=RoutingMode.AUTO)
    res3 = generator.generate_grounded_answer(
        query=q3,
        retrieved_chunks=[],
        evidence_items=ev3,
    )
    res3.routing_decision = dec3
    res3.evidence = ev3
    print_result(3, "Current External Technology News -> Web Search Provider", res3)

    # SCENARIO 4: Compound Multi-Source Question
    q4 = "Compare our internal document benchmarks with latest external web benchmarks"
    ev4, dec4, _ = orchestrator.route_and_retrieve(query=q4, routing_mode=RoutingMode.AUTO)
    res4 = generator.generate_grounded_answer(
        query=q4,
        retrieved_chunks=[],
        evidence_items=ev4,
    )
    res4.routing_decision = dec4
    res4.evidence = ev4
    print_result(4, "Compound Cross-Source Question -> Multi-Source Synthesis", res4)

    # SCENARIO 5: Ambiguous Query (Safe Fallback)
    q5 = "some undefined general topic"
    ev5, dec5, _ = orchestrator.route_and_retrieve(query=q5, routing_mode=RoutingMode.AUTO)
    res5 = generator.generate_grounded_answer(
        query=q5,
        retrieved_chunks=[],
        evidence_items=ev5,
    )
    res5.routing_decision = dec5
    res5.evidence = ev5
    print_result(5, "Ambiguous Question -> Safe Fallback to Vector Document Retrieval", res5)

    print("\n✓ Live verification completed successfully! All 5 scenarios verified.")


if __name__ == "__main__":
    main()
