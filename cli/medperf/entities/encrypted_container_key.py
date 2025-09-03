from __future__ import annotations
import os
import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import Any, TYPE_CHECKING, Optional
from pydantic import Field, root_validator, SecretBytes

from medperf.entities.interface import Entity
from medperf.account_management import get_medperf_user_data
from medperf import config
from medperf.exceptions import MissingPrivateKeyException, DecryptionError
from medperf.utils import get_pki_assets_path
from medperf.entities.ca import CA

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
    from medperf.entities.cube import Cube


def _get_default_padding():
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    )


class EncryptedContainerKey(Entity):
    """
    Class representing an Encrypted Container Key uploaded to the MedPerf server
    """

    encrypted_key: Optional[bytes] = Field(exclude=True)
    encrypted_key_base64: Optional[str]
    model_container: int
    certificate: int
    padding: padding.AsymmetricPadding = Field(
        default_factory=_get_default_padding, exclude=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ca = None

    class Config:
        arbitrary_types_allowed = True

    @root_validator(pre=False)
    def validate_encrypted_key(cls, values: dict[str, Any]):
        """
        If only one of encrypted_key_base64 or encrypted_key is provided,
        generate the other one via base64 encoding/decoding.
        If both are provided, verify they match. If not, raise a ValueError.
        If neither is provided, raise a ValueError.
        """
        content_base64 = values.get("encrypted_key_base64")
        content: bytes = values.get("encrypted_key")
        if content_base64 is None and content is None:
            raise ValueError(
                "One of encrypted_key_base64 or encrypted_key must be provided!"
            )

        elif content is not None:
            converted_content = base64.b64encode(content).decode("utf-8")
            if content_base64 is None:
                values["encrypted_key_base64"] = converted_content

            elif converted_content != content_base64:
                raise ValueError(
                    "The values provided for encrypted_key and encrypted_key_base64 do not match!"
                )

        elif content_base64 is not None:
            converted_base64 = base64.b64decode(content_base64)
            values["encrypted_key"] = converted_base64

        return values

    @staticmethod
    def get_type():
        return "encrypted_container_key"

    @staticmethod
    def get_storage_path():
        return config.container_keys_dir

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_encrypted_container_key

    @staticmethod
    def get_metadata_filename():
        return config.encrypted_container_key_metadata_filename

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_encrypted_container_key

    @property
    def local_id(self):
        return config.encrypted_container_key_file

    @property
    def path(self) -> str:
        return config.container_keys_dir

    @property
    def ca(self) -> CA:
        if self._ca is None:
            self._ca = CA.from_key(key_uid=self.id)
        return self._ca

    @classmethod
    def remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_encrypted_container_keys
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_encrypted_container_keys
        return comms_fn

    @classmethod
    def upload_many(
        cls, encrypted_container_key_list: list[EncryptedContainerKey]
    ) -> list[dict]:
        """Uploads many objects in a single operation on the server"""
        comms_fn = config.comms.upload_many_encrypted_keys
        list_as_dicts = [item.todict() for item in encrypted_container_key_list]
        updated_body = comms_fn(
            key_dict_list=list_as_dicts
        )
        return updated_body

    @classmethod
    def get_from_model(cls, model_id: int) -> EncryptedContainerKey:
        comms_fn = config.comms.get_encrypted_key_from_model_id
        key_body = comms_fn(model_id=model_id)
        return cls(**key_body)

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Certificate ID": self.certificate,
            "Model Containre ID": self.model_container,
            "Encrypted Key": self.encrypted_key,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }

    def decrypt_key(self, container: Cube) -> SecretBytes:
        decryption_key = self._load_private_key(container=container)
        try:
            decrypted_key = SecretBytes(decryption_key.decrypt(
                ciphertext=self.encrypted_key,
                padding=self.padding,
            ))
        except ValueError:
            raise DecryptionError(f'Could not decrypt keys to Container {container.name} (UID: {container.id})')
        return decrypted_key

    def _load_private_key(self, container: Cube) -> RSAPrivateKey:
        # TODO validate configs!
        # Are we doing PEM Private Keys, with no password and default_backend as implemented?
        # Are we going to support multiple configurations? If so, how?
        # What about padding? We a default, support multiple? If supporting multiple, how to config?

        user_email = get_medperf_user_data()["email"]
        pki_assets_dir = get_pki_assets_path(common_name=user_email, ca_name=self.ca.name)
        private_key_path = os.path.join(pki_assets_dir, config.private_key_file)

        if not os.path.exists(private_key_path):
            error_msg = (
                f"No private key was found locally for the user email {user_email} and "
                f"Certificate Authority (CA) {self.ca.name} (UID: {self.ca.id}), which enables "
                f"access to the Model Container {container.name} (UID: {container.id}).\n"
                f"Please run the following command to obtain a private key:\n"
                f"medperf certificate get_client_certificate --container-id {container.id}"
            )
            raise MissingPrivateKeyException(error_msg)

        with open(private_key_path, "rb") as private_key_file:
            private_bytes = private_key_file.read()

        private_key = serialization.load_pem_private_key(
            data=private_bytes, backend=default_backend(), password=None
        )

        return private_key
