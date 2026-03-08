from medperf.entities.schemas import UserSchema
from medperf.exceptions import MedperfException
from medperf.entities.utils import handle_validation_error


class User:
    """
    Class representing a User

    """

    @handle_validation_error
    def __init__(self, **kwargs):
        self._model = UserSchema(**kwargs)
        self.id = self._model.id
        self.username = self._model.username
        self.email = self._model.email
        self.first_name = self._model.first_name
        self.last_name = self._model.last_name
        self.metadata = self._model.metadata

    def get_cc_config(self):
        cc_values = self.metadata.get("cc", {})
        return cc_values.get("config", None)

    def set_cc_config(self, cc_config: dict):
        if "cc" not in self.metadata:
            self.metadata["cc"] = {}
        self.metadata["cc"]["config"] = cc_config

    def mark_cc_configured(self):
        if "cc" not in self.metadata:
            raise MedperfException(
                "User does not have a cc configuration to be marked as configured"
            )
        self.metadata["cc"]["configured"] = True

    def is_cc_configured(self):
        if "cc" not in self.metadata:
            return False
        return self.metadata["cc"].get("configured", False)
