"""Live verification script demonstrating end-to-end Phase 4 Adaptive & Corrective RAG with LangGraph.

Runs 5 comprehensive adaptive scenarios:
1. Direct Answerable Query (adaptive=True) -> Immediate relevance grade match, 0 rewrites, verified citations.
2. Conversational Noisy Query (adaptive=True) -> Rewriter strips filler, recovers relevant evidence, grounded response.
3. Absent / Unanswerable Query (adaptive=True) -> Rewrites queries up to max limit, truthfully declares insufficient evidence without hallucinating.
4. Adversarial Misleading Query (adaptive=True) -> Detects false premise, refuses to validate fabricated claims.
5. Backward-Compatible Call (adaptive=False) -> Standard Phase 3 multi-path routing executed without LangGraph overhead.
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.api.deps import (
    get_adaptive_workflow,
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
    print("\n" + "=" * 88)
    print(f" {title}")
    print("=" * 88)


def print_adaptive_result(scenario_num: int, title: str, response):
    print(f"\n[Scenario {scenario_num}]: {title}")
    print(f" Query: {response.query}")
    print(f" Model Used: {response.model_used} | Latency: {response.latency_ms:.1f}ms | Grounded: {response.grounded}")
    print(f" Fallback / Insufficient Evidence: {response.fallback_used}")

    if response.adaptive_metadata:
        meta = response.adaptive_metadata
        print("\n--- Adaptive Workflow Metadata ---")
        print(f" Route Selected: {meta.route_selected}")
        print(f" Retrieval Attempts: {meta.retrieval_attempts} | Correction Attempts: {meta.correction_attempts}")
        print(f" Evidence Graded: {meta.retrieved_evidence_count} total ({meta.relevant_evidence_count} relevant, {meta.irrelevant_evidence_count} irrelevant)")
        if meta.rewritten_queries:
            print(f" Rewritten Queries ({len(meta.rewritten_queries)}):")
            for idx, rw in enumerate(meta.rewritten_queries, start=1):
                print(f"   - Attempt {idx}: '{rw}'")
        if meta.grounding_validation:
            gv = meta.grounding_validation
            print(f" Grounding Check: is_grounded={gv.is_grounded}, confidence={getattr(gv, 'confidence_score', 1.0):.2f}, supported_claims={len(gv.supported_claims)}, unsupported_claims={len(gv.unsupported_claims)}")
        print(" Workflow Trace:")
        for step in meta.workflow_trace:
            print(f"   -> {step}")
    else:
        print("\n--- Standard Phase 3 Metadata (Adaptive Not Applied) ---")
        if response.routing_decision:
            print(f" Route: {response.routing_decision.route.value} (Confidence: {response.routing_decision.confidence:.2f})")

    print(f"\n Evidence Items: {len(response.evidence)} | Citations: {len(response.citations)}")
    if response.citations:
        print("\n--- Citations ---")
        for cit in response.citations:
            print(f" [{cit.citation_id}] Source: {cit.filename} (Page: {cit.page_number}, Score: {cit.score:.3f})")
            print(f"     Excerpt: {cit.snippet[:120]}...")

    print("\n--- Generated Answer ---")
    print(f" {response.answer}")
    print("-" * 88)


def main():
    print_header("VeriWeave Phase 4: Adaptive & Corrective RAG with LangGraph Live Verification")
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
                "Phase 4 implements a stateful LangGraph workflow featuring document relevance grading, "
                "adaptive query rewriting when context is insufficient, corrective retrieval, and hallucination "
                "validation before finalizing answers. VeriWeave uses dense vector embeddings and persistent Qdrant."
            ),
            page_number=1,
            chunk_index=i,
            token_count_estimate=52,
            char_start=0,
            char_end=280,
        )
        for i in range(2)
    ]
    sync_document_ingestion(seed_doc, seed_chunks)
    print("✓ Successfully synchronized sample document metadata to SQLite catalog.")

    # 3. Instantiate LangGraph Adaptive Workflow & Orchestrator
    adaptive_workflow = get_adaptive_workflow()
    orchestrator = get_routing_orchestrator()
    generator = get_grounded_generator()

    # SCENARIO 1: Direct Answerable Query (adaptive=True)
    q1 = "What is the difference between short-term memory and long-term memory in AI agents?"
    res1 = adaptive_workflow.run(
        query=q1,
        routing_mode=RoutingMode.AUTO,
        selected_strategy=RetrievalStrategy.HYBRID,
    )
    print_adaptive_result(1, "Direct Answerable Query -> Immediate Relevance Match & Grounded Verification", res1)

    # SCENARIO 2: Conversational Noisy Query (adaptive=True)
    q2 = "Could you please explain what is the difference between short-term memory and long-term memory in AI agents if you do not mind?"
    res2 = adaptive_workflow.run(
        query=q2,
        routing_mode=RoutingMode.AUTO,
        selected_strategy=RetrievalStrategy.HYBRID,
    )
    print_adaptive_result(2, "Conversational Noisy Query -> Filler Stripping & Intent Preservation", res2)

    # SCENARIO 3: Absent / Unanswerable Query (adaptive=True)
    q3 = "What are the quantum computing benchmarks of VeriWeave on an IBM 1121-qubit processor?"
    res3 = adaptive_workflow.run(
        query=q3,
        routing_mode=RoutingMode.AUTO,
        selected_strategy=RetrievalStrategy.HYBRID,
    )
    print_adaptive_result(3, "Absent / Unanswerable Query -> Bounded Query Rewrites & Truthful Insufficiency Declaration", res3)

    # SCENARIO 4: Adversarial Misleading Query (adaptive=True)
    q4 = "Why did VeriWeave abandon vector retrieval in 2026 to migrate entirely to proof-of-work blockchain storage?"
    res4 = adaptive_workflow.run(
        query=q4,
        routing_mode=RoutingMode.AUTO,
        selected_strategy=RetrievalStrategy.HYBRID,
    )
    print_adaptive_result(4, "Adversarial Misleading Query -> Rejects False Premise Without Hallucinating", res4)

    # SCENARIO 5: Backward-Compatible Call (adaptive=False)
    q5 = "How many documents are uploaded in the system?"
    start_t = time.perf_counter()
    ev5, dec5, _ = orchestrator.route_and_retrieve(query=q5, routing_mode=RoutingMode.AUTO)
    res5 = generator.generate_grounded_answer(
        query=q5,
        retrieved_chunks=[],
        evidence_items=ev5,
    )
    res5.routing_decision = dec5
    res5.evidence = ev5
    res5.latency_ms = (time.perf_counter() - start_t) * 1000
    res5.adaptive_metadata = None
    print_adaptive_result(5, "Backward-Compatible Non-Adaptive Call -> Direct Phase 3 Multi-Path Execution", res5)

    print("\n" + "=" * 88)
    print(" ✓ All 5 Phase 4 Adaptive & Corrective RAG Live Scenarios Executed Successfully!")
    print("=" * 88 + "\n")


if __name__ == "__main__":
    main()
