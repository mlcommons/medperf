from medperf import config
from medperf.utils import approval_prompt, generate_container_key_redaction_record
from medperf.exceptions import CleanExit
from medperf.entities.encrypted_container_key import EncryptedContainerKey


class DeleteKeys:
    @classmethod
    def run(cls, model_id, approved=False):
        grantaccess = cls(model_id, approved)
        grantaccess.get_approval()
        grantaccess.revoke_access()

    def __init__(self, model_id: int, approved: bool = False):
        self.model_id = model_id
        self.approved = approved

    def get_approval(self):
        msg = (
            "Please confirm that you wish to revoke access to the "
            f"model {self.model_id} by deleting all its keys."
        )

        if not self.approved and not approval_prompt(msg):
            raise CleanExit("Key deletion operation cancelled")

    def revoke_access(self):
        keys = EncryptedContainerKey.get_user_keys()
        keys = [key for key in keys if key.container == self.model_id]
        bodies = {
            key.id: {
                "is_valid": False,
                "encrypted_key_base64": generate_container_key_redaction_record(
                    key.encrypted_key_base64
                ),
            }
            for key in keys
        }
        del keys
        config.comms.update_many_container_keys(bodies)
