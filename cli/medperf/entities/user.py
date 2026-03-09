from medperf.entities.schemas import UserSchema
from medperf.entities.utils import handle_validation_error


class User:
    """
    Class representing a User

    """

    @handle_validation_error
    def __init__(self, **kwargs):
        self._model = UserSchema(**kwargs)
        self._fields = list(self._model.__fields__.keys())
        self.id = self._model.id
        self.username = self._model.username
        self.email = self._model.email
        self.first_name = self._model.first_name
        self.last_name = self._model.last_name
        self.metadata = self._model.metadata

    def __setattr__(self, name, value):
        if (
            hasattr(self, "_model")
            and hasattr(self, "_fields")
            and name in self._fields
        ):
            setattr(self._model, name, value)
        super().__setattr__(name, value)

    def get_cc_config(self):
        cc_values = self.metadata.get("cc", {})
        return cc_values.get("config", {})

    def set_cc_config(self, cc_config: dict):
        if "cc" not in self.metadata:
            self.metadata["cc"] = {}
        self.metadata["cc"]["config"] = cc_config

    def is_cc_configured(self):
        return self.get_cc_config() != {}
