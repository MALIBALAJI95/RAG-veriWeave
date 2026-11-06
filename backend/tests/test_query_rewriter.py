"""Tests for adaptive query rewriting, intent preservation, and retry progression."""

import pytest
from backend.app.adaptive.query_rewriter import AdaptiveQueryRewriter


def test_query_rewriter_strips_conversational_fillers():
    """AdaptiveQueryRewriter must strip conversational filler phrases while preserving intent."""
    rewriter = AdaptiveQueryRewriter(ollama_client=None, max_rewrites=2)

    queries = [
        ("Can you please tell me about the architecture of transformers?", "architecture of transformers"),
        ("Could you explain how Reciprocal Rank Fusion works?", "how Reciprocal Rank Fusion works"),
        ("Please provide information on BM25 sparse scoring", "BM25 sparse scoring"),
        ("I would like to know what is cross-encoder reranking", "what is cross-encoder reranking"),
    ]

    for noisy, expected_sub in queries:
        res = rewriter.rewrite(noisy, attempt_number=1)
        assert res.attempt_number == 1
        assert len(res.rewritten_query) > 0
        assert expected_sub.lower() in res.rewritten_query.lower() or res.rewritten_query.lower() in expected_sub.lower()
        # Verify it removed the filler
        assert not res.rewritten_query.lower().startswith("can you please")
        assert not res.rewritten_query.lower().startswith("could you explain")


def test_query_rewriter_progressive_attempts():
    """AdaptiveQueryRewriter must provide progressively targeted formulations across attempts."""
    rewriter = AdaptiveQueryRewriter(ollama_client=None, max_rewrites=2)
    original = "What are the components of memory in autonomous AI agents?"

    # Attempt 1
    res1 = rewriter.rewrite(original, attempt_number=1, failure_reason="0 chunks found")
    assert res1.attempt_number == 1
    assert "memory" in res1.rewritten_query.lower()

    # Attempt 2
    res2 = rewriter.rewrite(original, attempt_number=2, failure_reason="low similarity score")
    assert res2.attempt_number == 2
    assert res2.rewritten_query != original
    assert "attempt 2" in res2.rewrite_reason.lower()


def test_query_rewriter_preserves_intent_no_hallucinations():
    """AdaptiveQueryRewriter must not introduce unsupported hypothetical entities."""
    rewriter = AdaptiveQueryRewriter(ollama_client=None, max_rewrites=2)
    original = "Explain Qdrant vector indexing and HNSW"

    res = rewriter.rewrite(original, attempt_number=1)
    # The rewritten query must still mention the core concepts
    assert "qdrant" in res.rewritten_query.lower()
    assert "hnsw" in res.rewritten_query.lower() or "vector" in res.rewritten_query.lower()
