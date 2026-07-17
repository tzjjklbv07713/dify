from __future__ import annotations

from dev.model_hub_provider_plugin_package.src.model_hub_provider.vector_normalizer import (
    normalize_embedding_response,
    normalize_rerank_response,
)


def test_normalize_embedding_response_maps_openai_shape() -> None:
    result = normalize_embedding_response(
        payload={
            "model": "text-embedding-3-large",
            "data": [
                {"embedding": [0.1, 0.2]},
                {"embedding": [0.3, 0.4]},
            ],
            "usage": {"prompt_tokens": 12, "total_tokens": 12},
        },
        fallback_model="fallback-model",
    )

    assert result.model == "text-embedding-3-large"
    assert result.embeddings == [[0.1, 0.2], [0.3, 0.4]]
    assert result.usage.total_tokens == 12


def test_normalize_rerank_response_maps_scores_and_indexes() -> None:
    result = normalize_rerank_response(
        payload={
            "model": "rerank-v1",
            "results": [
                {"index": 1, "relevance_score": 0.95},
                {"index": 0, "relevance_score": 0.80},
            ],
        },
        documents=["doc-0", "doc-1"],
        fallback_model="fallback-model",
    )

    assert result.model == "rerank-v1"
    assert result.docs[0].index == 1
    assert result.docs[0].text == "doc-1"
    assert result.docs[0].score == 0.95
