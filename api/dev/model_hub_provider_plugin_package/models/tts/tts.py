from dify_plugin.interfaces.model.openai_compatible.tts import OAICompatText2SpeechModel

from ..common_model_hub import assert_model_available


class ModelHubTextToSpeechModel(OAICompatText2SpeechModel):
    def validate_credentials(self, model: str, credentials: dict) -> None:
        assert_model_available(model, credentials)
