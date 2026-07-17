"""Normalize embedding / rerank proxy responses into Dify runtime entities."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from graphon.model_runtime.entities.rerank_entities import RerankDocument, RerankResult
from graphon.model_runtime.entities.text_embedding_entities import EmbeddingResult, EmbeddingUsage


def normalize_embedding_response(*, payload: dict[str, Any], fallback_model: str) -> EmbeddingResult:
    data = payload.get("data") or []
    embeddings = [
        item.get("embedding") for item in data if isinstance(item, dict) and isinstance(item.get("embedding"), list)
    ]
    usage_payload = payload.get("usage") or {}
    usage = EmbeddingUsage(
        tokens=int(usage_payload.get("prompt_tokens") or usage_payload.get("tokens") or 0),
        total_tokens=int(usage_payload.get("total_tokens") or usage_payload.get("tokens") or 0),
        unit_price=Decimal(0),
        price_unit=Decimal(0),
        total_price=Decimal(0),
        currency="USD",
        latency=float(usage_payload.get("latency") or 0),
    )
    return EmbeddingResult(
        model=str(payload.get("model") or fallback_model),
        embeddings=embeddings,
        usage=usage,
    )


def normalize_rerank_response(*, payload: dict[str, Any], documents: list[str], fallback_model: str) -> RerankResult:
    results = payload.get("results") or payload.get("data") or []
    rerank_docs = []
    for index, item in enumerate(results):
        if not isinstance(item, dict):
            continue
        doc_index = int(item.get("index", index))
        text = documents[doc_index] if 0 <= doc_index < len(documents) else str(item.get("text") or "")
        rerank_docs.append(
            RerankDocument(
                index=doc_index,
                text=text,
                score=float(item.get("relevance_score") or item.get("score") or 0),
            )
        )
    return RerankResult(
        model=str(payload.get("model") or fallback_model),
        docs=rerank_docs,
    )
