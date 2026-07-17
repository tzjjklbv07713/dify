from dify_plugin.interfaces.model.openai_compatible.text_embedding import OAICompatEmbeddingModel

from ..common_model_hub import assert_model_available


class ModelHubTextEmbeddingModel(OAICompatEmbeddingModel):
    def validate_credentials(self, model: str, credentials: dict) -> None:
        assert_model_available(model, credentials)
