from __future__ import annotations
import base64
from medperf.entities.schemas import MedperfSchema
from medperf import config
from medperf.exceptions import MedperfException
from medperf.commands.certificate.utils import (
    current_user_certificate_status,
    load_user_private_key,
)
from medperf.encryption import AsymmetricEncryption
from medperf.utils import get_decryption_key_path, secure_write_to_file
from typing import List


class EncryptedContainerKey(MedperfSchema):
    """
    Class representing an Encrypted Container Key
    """

    encrypted_key_base64: str
    container: int
    certificate: int

    @classmethod
    def get(cls, key_id: int) -> EncryptedContainerKey:
        """Uploads many objects in a single operation on the server"""
        comms_fn = config.comms.get_container_key
        entity = comms_fn(key_id)
        return EncryptedContainerKey(**entity)

    @classmethod
    def get_user_keys(cls) -> List[EncryptedContainerKey]:
        """Uploads many objects in a single operation on the server"""
        comms_fn = config.comms.get_user_keys
        entities = comms_fn()

        return [EncryptedContainerKey(**entity) for entity in entities]

    @classmethod
    def upload_many(
        cls, encrypted_container_key_list: list[EncryptedContainerKey]
    ) -> list[dict]:
        """Uploads many objects in a single operation on the server"""
        comms_fn = config.comms.upload_many_encrypted_keys
        list_as_dicts = [item.todict() for item in encrypted_container_key_list]
        updated_body = comms_fn(key_dict_list=list_as_dicts)
        return updated_body

    @classmethod
    def get_user_key_for_model(cls, model_id: int) -> EncryptedContainerKey:
        # Get user cert
        user_cert_info = current_user_certificate_status()
        if not user_cert_info["no_action_required"]:
            raise MedperfException("You don't have a valid certificate")
        user_cert = user_cert_info["user_cert_object"]

        # Get model key
        filters = {"container": model_id, "certificate": user_cert.id, "is_valid": True}
        keys = config.comms.get_user_keys(filters=filters)
        if len(keys) == 0:
            raise MedperfException(f"You don't have access to the container {model_id}")

        if len(keys) > 1:
            raise MedperfException("Internal error: expected only one key.")

        key = keys[0]
        return EncryptedContainerKey(**key)

    def decrypt(self):
        output_path = get_decryption_key_path(self.container)
        encrypted_key_bytes = base64.b64decode(self.encrypted_key_base64)
        private_key_bytes = load_user_private_key()
        decrypted_key_bytes = AsymmetricEncryption().decrypt(
            private_key_bytes, encrypted_key_bytes
        )
        del private_key_bytes
        secure_write_to_file(
            output_path, decrypted_key_bytes, binary=True, exec_permission=True
        )
        del decrypted_key_bytes
        return output_path

    def display_dict(self):
        return {
            "UID": self.id,
            "Name": self.name,
            "Certificate ID": self.certificate,
            "Container ID": self.container,
            "Created At": self.created_at,
        }
