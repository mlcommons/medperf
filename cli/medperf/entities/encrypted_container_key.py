from __future__ import annotations
import base64
import logging
from medperf.entities.schemas import MedperfSchema
from medperf import config
from medperf.exceptions import (
    MedperfException,
    DecryptionError,
    PrivateContainerAccessError,
)
from medperf.commands.certificate.utils import (
    current_user_certificate_status,
    load_user_private_key,
)
from medperf.encryption import AsymmetricEncryption
from medperf.utils import get_decryption_key_path, secure_write_to_file
from typing import List


class EncryptedKey(MedperfSchema):
    """
    Class representing an Encrypted Container Key
    """

    encrypted_key_base64: str
    container: int
    certificate: int

    @classmethod
    def get(cls, key_id: int) -> EncryptedKey:
        """Get an encrypted key object"""
        entity = config.comms.get_encrypted_key(key_id)
        return EncryptedKey(**entity)

    @classmethod
    def get_container_keys(cls, container_id) -> List[EncryptedKey]:
        """Get encrypted keys of a container"""
        filters = {"container": container_id}
        entities = config.comms.get_user_encrypted_keys(filters)

        return [EncryptedKey(**entity) for entity in entities]

    @classmethod
    def get_user_container_key(cls, container_id: int) -> EncryptedKey:
        """Get encrypted key of a container for the current user certificate"""
        # Get user cert
        user_cert_info = current_user_certificate_status()
        if not user_cert_info["no_action_required"]:
            raise PrivateContainerAccessError("You don't have a valid certificate")
        user_cert = user_cert_info["user_cert_object"]

        # Get model key
        filters = {"container": container_id, "certificate": user_cert.id}
        keys = config.comms.get_user_encrypted_keys(filters=filters)
        if len(keys) == 0:
            raise PrivateContainerAccessError(
                f"You don't have access to the container {container_id}"
            )

        if len(keys) > 1:
            raise MedperfException("Internal error: expected only one key.")

        return EncryptedKey(**keys[0])

    @classmethod
    def upload_many(cls, encrypted_key_list: list[EncryptedKey]) -> list[dict]:
        """Uploads many objects in a single operation on the server"""
        list_as_dicts = [item.todict() for item in encrypted_key_list]
        updated_body = config.comms.upload_many_encrypted_keys(list_as_dicts)
        return updated_body

    def decrypt(self):
        logging.debug("Decrypting key.")
        output_path = get_decryption_key_path(self.container)
        logging.debug(f"Output path: {output_path}")
        encrypted_key_bytes = base64.b64decode(self.encrypted_key_base64)
        private_key_bytes = load_user_private_key()
        if private_key_bytes is None:
            raise DecryptionError("Missing Private Key")
        decrypted_key_bytes = AsymmetricEncryption().decrypt(
            private_key_bytes, encrypted_key_bytes
        )
        secure_write_to_file(
            output_path, decrypted_key_bytes, binary=True, exec_permission=True
        )
        return output_path

    def display_dict(self):
        return {
            "UID": self.id,
            "Name": self.name,
            "Certificate ID": self.certificate,
            "Container ID": self.container,
            "Created At": self.created_at,
        }
