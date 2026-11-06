"""Unit tests for Reciprocal Rank Fusion (RRF) engine."""

import pytest
from backend.app.retrieval.fusion import RRFFusionEngine
from backend.app.schemas.chat import RetrievedChunk


def make_chunk(chunk_id: str, doc_id: str = "doc_1", score: float = 0.5) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        filename="test.txt",
        page_number=1,
        chunk_index=0,
        text=f"Text for {chunk_id}",
        score=score,
    )


def test_rrf_mathematical_correctness():
    engine = RRFFusionEngine(k=60)

    c1 = make_chunk("c1", score=0.9)
    c2 = make_chunk("c2", score=0.8)
    c3 = make_chunk("c3", score=0.7)

    # List 1: c1 (rank 1), c2 (rank 2)
    # List 2: c2 (rank 1), c3 (rank 2)
    list1 = [c1, c2]
    list2 = [c2, c3]

    fused = engine.fuse([list1, list2], top_k=3)

    # c2 appears in both lists: rank 2 in list1, rank 1 in list2
    # expected score: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.016129 + 0.016393 = 0.032522
    expected_c2_score = round(1.0 / 62 + 1.0 / 61, 5)

    # c1 appears only in list1 at rank 1: 1/(60+1) = 1/61 = 0.016393
    expected_c1_score = round(1.0 / 61, 5)

    assert len(fused) == 3
    # c2 must be ranked first because it appears in both lists
    assert fused[0].chunk_id == "c2"
    assert fused[0].score == expected_c2_score
    assert fused[1].chunk_id == "c1"
    assert fused[1].score == expected_c1_score


def test_rrf_provenance_tracking():
    engine = RRFFusionEngine(k=60)
    c1 = make_chunk("c1", score=0.95)
    c2 = make_chunk("c2", score=0.75)

    list1 = [c1, c2]
    list2 = [c1]

    fused = engine.fuse([list1, list2], top_k=2, source_labels=["dense", "sparse"])
    assert fused[0].chunk_id == "c1"
    meta = fused[0].metadata
    assert "rrf_ranks" in meta
    assert meta["rrf_ranks"]["dense"] == 1
    assert meta["rrf_ranks"]["sparse"] == 1
    assert "rrf_source_scores" in meta
    assert meta["rrf_source_scores"]["dense"] == 0.95


def test_rrf_empty_inputs():
    engine = RRFFusionEngine(k=60)
    assert engine.fuse([]) == []
    assert engine.fuse([[], []]) == []


def test_rrf_invalid_k():
    with pytest.raises(ValueError):
        RRFFusionEngine(k=0)
    with pytest.raises(ValueError):
        RRFFusionEngine(k=-10)
