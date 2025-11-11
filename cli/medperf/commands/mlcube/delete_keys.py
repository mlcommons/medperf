from medperf import config
from medperf.utils import approval_prompt, generate_container_key_redaction_record
from medperf.exceptions import CleanExit
from medperf.entities.encrypted_container_key import EncryptedKey
import logging


class DeleteKeys:
    @classmethod
    def run(cls, container_id, approved=False):
        grantaccess = cls(container_id, approved)
        grantaccess.get_approval()
        grantaccess.revoke_access()

    def __init__(self, container_id: int, approved: bool = False):
        self.container_id = container_id
        self.approved = approved

    def get_approval(self):
        msg = (
            "Please confirm that you wish to revoke access to the "
            f"container {self.container_id} by deleting all its keys."
        )

        if not self.approved and not approval_prompt(msg):
            raise CleanExit("Key deletion operation cancelled")

    def revoke_access(self):
        keys = EncryptedKey.get_container_keys(self.container_id)
        bodies = [
            {
                "id": key.id,
                "is_valid": False,
                "encrypted_key_base64": generate_container_key_redaction_record(
                    key.encrypted_key_base64
                ),
            }
            for key in keys
        ]
        logging.debug(f"Keys to delete: {[body['id'] for body in bodies]}")
        config.comms.update_many_encrypted_keys(bodies)
