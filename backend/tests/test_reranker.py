"""Unit tests for Cross-Encoder reranking component."""

from backend.app.retrieval.reranker import CrossEncoderReranker, sigmoid
from backend.app.schemas.chat import RetrievedChunk


def test_sigmoid():
    assert sigmoid(0.0) == 0.5
    assert sigmoid(10.0) > 0.99
    assert sigmoid(-10.0) < 0.01


def test_cross_encoder_reranking_ordering():
    reranker = CrossEncoderReranker(
        model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
        device="cpu",
        enabled=True,
    )

    query = "What is Reciprocal Rank Fusion?"

    chunks = [
        RetrievedChunk(
            chunk_id="c_irrelevant",
            doc_id="d1",
            filename="fruits.txt",
            page_number=1,
            chunk_index=0,
            text="Apples and bananas are nutritious fruits rich in fiber and vitamins.",
            score=0.9,  # Artificially high initial score
            original_rank=1,
        ),
        RetrievedChunk(
            chunk_id="c_relevant",
            doc_id="d2",
            filename="fusion.txt",
            page_number=1,
            chunk_index=0,
            text="Reciprocal Rank Fusion (RRF) is an algorithm that combines multiple ranked lists into a single consolidated ranking.",
            score=0.4,  # Artificially low initial score
            original_rank=2,
        ),
    ]

    reranked = reranker.rerank(query=query, chunks=chunks, top_k=2)

    assert len(reranked) == 2
    # The relevant passage must be reranked to rank 1 by the cross-encoder!
    assert reranked[0].chunk_id == "c_relevant"
    assert reranked[0].original_rank == 1
    assert reranked[0].rerank_score is not None
    assert reranked[0].rerank_score > reranked[1].rerank_score
    assert "pre_rerank_rank" in reranked[0].metadata
    assert reranked[0].metadata["pre_rerank_rank"] == 2


def test_cross_encoder_disabled():
    reranker = CrossEncoderReranker(enabled=False)
    chunks = [
        RetrievedChunk(
            chunk_id="c1",
            doc_id="d1",
            filename="f.txt",
            page_number=1,
            chunk_index=0,
            text="Some text",
            score=0.8,
            original_rank=1,
        )
    ]
    res = reranker.rerank("Query", chunks, top_k=1)
    assert res[0].score == 0.8
    assert res[0].rerank_score is None
