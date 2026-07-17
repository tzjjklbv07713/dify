from dify_plugin.interfaces.model.openai_compatible.speech2text import OAICompatSpeech2TextModel

from ..common_model_hub import assert_model_available


class ModelHubSpeech2TextModel(OAICompatSpeech2TextModel):
    def validate_credentials(self, model: str, credentials: dict) -> None:
        assert_model_available(model, credentials)
