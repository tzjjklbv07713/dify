import logging
from collections.abc import Mapping

from dify_plugin import ModelProvider
from dify_plugin.errors.model import CredentialsValidateFailedError
from models.common_model_hub import list_remote_models

logger = logging.getLogger(__name__)


class ModelHubProvider(ModelProvider):
    def validate_provider_credentials(self, credentials: Mapping) -> None:
        try:
            list_remote_models(credentials)
        except Exception as error:
            raise CredentialsValidateFailedError(f"Unable to fetch models: {error}") from error
