from dify_plugin.interfaces.model.openai_compatible.rerank import OAICompatRerankModel

from ..common_model_hub import assert_model_available


class ModelHubRerankModel(OAICompatRerankModel):
    def validate_credentials(self, model: str, credentials: dict) -> None:
        assert_model_available(model, credentials)
