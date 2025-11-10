from medperf import config
from medperf.utils import approval_prompt, generate_container_key_redaction_record
from medperf.exceptions import CleanExit
from medperf.entities.encrypted_container_key import EncryptedKey


class RevokeUserAccess:
    @classmethod
    def run(cls, key_id, approved=False):
        grantaccess = cls(key_id, approved)
        grantaccess.get_approval()
        grantaccess.revoke_access()

    def __init__(self, key_id: int, approved: bool = False):
        self.key_id = key_id
        self.approved = approved

    def get_approval(self):
        msg = (
            "Please confirm that you wish to revoke access to the "
            f"user by deleting the key {self.key_id}"
        )

        if not self.approved and not approval_prompt(msg):
            raise CleanExit("Access revoking operation cancelled")

    def revoke_access(self):
        key = EncryptedKey.Get(self.key_id)
        redaction_record = generate_container_key_redaction_record(
            key.encrypted_key_base64
        )
        body = {"is_valid": False, "encrypted_key_base64": redaction_record}
        config.comms.update_encrypted_key(self.key_id, body)
