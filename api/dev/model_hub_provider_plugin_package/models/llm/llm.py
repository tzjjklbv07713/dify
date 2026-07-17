from dify_plugin.interfaces.model.openai_compatible.llm import OAICompatLargeLanguageModel

from ..common_model_hub import assert_model_available


class ModelHubLargeLanguageModel(OAICompatLargeLanguageModel):
    def validate_credentials(self, model: str, credentials: dict) -> None:
        assert_model_available(model, credentials)
