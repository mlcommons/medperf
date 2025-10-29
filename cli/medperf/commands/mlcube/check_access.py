from medperf.entities.encrypted_container_key import EncryptedContainerKey


class CheckAccess:
    @classmethod
    def run(cls, model_id):
        key = EncryptedContainerKey.get_user_key_for_model(model_id)
        del key
