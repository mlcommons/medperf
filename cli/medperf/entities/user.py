from pydantic import BaseModel
from medperf.exceptions import MedperfException


class User(BaseModel):
    """
    Class representing a User

    """

    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    metadata: dict = {}

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
