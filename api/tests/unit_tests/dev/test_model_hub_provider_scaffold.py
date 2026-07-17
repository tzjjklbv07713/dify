from __future__ import annotations

from dev.model_hub_provider_scaffold.catalog_client import ModelHubCatalogClient
from dev.model_hub_provider_scaffold.provider_schema import PROVIDER_ID, build_model_hub_provider_entity
from graphon.model_runtime.entities.model_entities import FetchFrom, ModelType
from graphon.model_runtime.entities.provider_entities import ConfigurateMethod


def test_build_model_hub_provider_entity_exposes_expected_identity_and_methods() -> None:
    provider = build_model_hub_provider_entity()

    assert provider.provider == PROVIDER_ID
    assert provider.provider_name == "model-hub"
    assert ConfigurateMethod.PREDEFINED_MODEL in provider.configurate_methods
    assert ConfigurateMethod.CUSTOMIZABLE_MODEL in provider.configurate_methods
    assert ModelType.LLM in provider.supported_model_types
    assert ModelType.TEXT_EMBEDDING in provider.supported_model_types


def test_catalog_client_builds_expected_urls() -> None:
    client = ModelHubCatalogClient(
        credentials={
            "proxy_base_url": "https://proxy.example.com/",
            "proxy_api_key": "secret",
        }
    )

    assert client.build_ping_url() == "https://proxy.example.com/provider/ping"
    assert client.build_models_url() == "https://proxy.example.com/provider/models"


def test_catalog_client_normalizes_remote_model_entity() -> None:
    client = ModelHubCatalogClient(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    entity = client._to_model_entity(
        {
            "id": "claude-3-5-sonnet",
            "type": "llm",
            "label": "Claude 3.5 Sonnet",
            "features": ["tool-call", "structured-output"],
            "mode": "chat",
            "context_size": 200000,
        }
    )

    assert entity.model == "claude-3-5-sonnet"
    assert entity.model_type == ModelType.LLM
    assert entity.fetch_from == FetchFrom.PREDEFINED_MODEL
    assert entity.model_properties
