from medperf.entities.encrypted_container_key import EncryptedKey
from medperf import config


class CheckAccess:
    @classmethod
    def run(cls, model_id):
        EncryptedKey.get_user_container_key(model_id)
        config.ui.print("You are authorized to access the container")
