"""Provider declaration scaffold for a custom model-hub provider.

The future external plugin package should expose an equivalent ``ProviderEntity``
so Dify can render:

- a custom provider name / icon / help link
- provider-level credentials for the proxy endpoint
- remote model discovery
- optional manual model fallback
"""

from __future__ import annotations

from graphon.model_runtime.entities.common_entities import I18nObject
from graphon.model_runtime.entities.model_entities import ModelType
from graphon.model_runtime.entities.provider_entities import (
    ConfigurateMethod,
    CredentialFormSchema,
    FieldModelSchema,
    FormOption,
    FormType,
    ModelCredentialSchema,
    ProviderCredentialSchema,
    ProviderEntity,
)

PROVIDER_ID = "your-company/model-hub/proxy"


def build_model_hub_provider_entity() -> ProviderEntity:
    """Return the target provider declaration for the custom proxy plugin."""

    provider_credential_schema = ProviderCredentialSchema(
        credential_form_schemas=[
            CredentialFormSchema(
                variable="proxy_base_url",
                label=I18nObject(en_US="Proxy Base URL", zh_Hans="中转站 Base URL"),
                type=FormType.TEXT_INPUT,
                required=True,
                placeholder=I18nObject(
                    en_US="https://model-hub.example.com",
                    zh_Hans="https://model-hub.example.com",
                ),
            ),
            CredentialFormSchema(
                variable="proxy_api_key",
                label=I18nObject(en_US="Proxy API Key", zh_Hans="中转站 API Key"),
                type=FormType.SECRET_INPUT,
                required=True,
            ),
            CredentialFormSchema(
                variable="catalog_path",
                label=I18nObject(en_US="Catalog Path", zh_Hans="模型目录路径"),
                type=FormType.TEXT_INPUT,
                required=False,
                default="/provider/models",
                placeholder=I18nObject(en_US="/provider/models", zh_Hans="/provider/models"),
            ),
            CredentialFormSchema(
                variable="api_protocol",
                label=I18nObject(en_US="API Protocol", zh_Hans="API 协议"),
                type=FormType.SELECT,
                required=False,
                default="responses",
                options=[
                    FormOption(
                        value="responses",
                        label=I18nObject(en_US="Responses API", zh_Hans="Responses API"),
                    ),
                    FormOption(
                        value="chat_completions",
                        label=I18nObject(en_US="Chat Completions", zh_Hans="Chat Completions"),
                    ),
                ],
            ),
            CredentialFormSchema(
                variable="routing_group",
                label=I18nObject(en_US="Routing Group", zh_Hans="路由分组"),
                type=FormType.TEXT_INPUT,
                required=False,
                placeholder=I18nObject(en_US="production", zh_Hans="production"),
            ),
            CredentialFormSchema(
                variable="timeout_ms",
                label=I18nObject(en_US="Timeout (ms)", zh_Hans="超时毫秒"),
                type=FormType.TEXT_INPUT,
                required=False,
                default="15000",
            ),
            CredentialFormSchema(
                variable="validation_model",
                label=I18nObject(en_US="Validation Model", zh_Hans="校验模型"),
                type=FormType.TEXT_INPUT,
                required=False,
                placeholder=I18nObject(en_US="gpt-5.5", zh_Hans="gpt-5.5"),
            ),
        ]
    )

    model_credential_schema = ModelCredentialSchema(
        model=FieldModelSchema(
            label=I18nObject(en_US="Model Name", zh_Hans="模型名"),
            placeholder=I18nObject(
                en_US="claude-3-5-sonnet / gemini-2.5-pro / deepseek-chat ...",
                zh_Hans="claude-3-5-sonnet / gemini-2.5-pro / deepseek-chat ...",
            ),
        ),
        credential_form_schemas=[],
    )

    return ProviderEntity(
        provider=PROVIDER_ID,
        provider_name="model-hub",
        label=I18nObject(en_US="Model Hub", zh_Hans="模型中转站"),
        description=I18nObject(
            en_US="Third-party proxy provider that discovers and routes multiple upstream model vendors.",
            zh_Hans="聚合多家底层模型厂商的第三方中转站 Provider。",
        ),
        icon_small=I18nObject(
            en_US="https://placeholder.invalid/model-hub/icon-small.png",
            zh_Hans="https://placeholder.invalid/model-hub/icon-small.png",
        ),
        icon_small_dark=I18nObject(
            en_US="https://placeholder.invalid/model-hub/icon-small-dark.png",
            zh_Hans="https://placeholder.invalid/model-hub/icon-small-dark.png",
        ),
        supported_model_types=[
            ModelType.LLM,
            ModelType.TEXT_EMBEDDING,
            ModelType.RERANK,
            ModelType.SPEECH2TEXT,
            ModelType.TTS,
        ],
        configurate_methods=[
            ConfigurateMethod.PREDEFINED_MODEL,
            ConfigurateMethod.CUSTOMIZABLE_MODEL,
        ],
        provider_credential_schema=provider_credential_schema,
        model_credential_schema=model_credential_schema,
        models=[],
    )
