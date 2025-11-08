from medperf.entities.encrypted_container_key import EncryptedKey
from medperf import config


class CheckAccess:
    @classmethod
    def run(cls, model_id):
        key = EncryptedKey.get_user_container_key(model_id)
        del key
        config.ui.print("You are authorized to access the container")
