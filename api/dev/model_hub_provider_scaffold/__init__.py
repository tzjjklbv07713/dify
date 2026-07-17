"""Scaffold helpers for a custom third-party model-hub provider plugin.

This package does not register a live Dify plugin by itself. It is a source
scaffold that codifies:

1. the provider declaration we want the plugin to expose
2. the remote catalog / validation contract the proxy should implement
3. the normalization rules that map proxy model records into Dify model entities

It exists so we can iterate on one concrete contract in-repo before wiring it
into the external plugin packaging / publishing toolchain.
"""

from .catalog_client import ModelHubCatalogClient
from .provider_schema import build_model_hub_provider_entity

__all__ = [
    "ModelHubCatalogClient",
    "build_model_hub_provider_entity",
]
