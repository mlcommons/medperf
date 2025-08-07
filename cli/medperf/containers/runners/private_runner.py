from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Union
import os
from cryptography.fernet import Fernet

from .runner import Runner
from .decryption_utils import (
    load_private_key_info,
    load_encrypted_symmetric_key_and_delete,
)

from medperf import config
from medperf.comms.entity_resources import resources
from medperf.entities.ca import CA
from medperf.exceptions import CommunicationRetrievalError
from medperf.utils import remove_path, get_container_key_dir_path


if TYPE_CHECKING:
    from medperf.entities.cube import Cube


class PrivateRunner(Runner):
    def __init__(
        self, container_config_parser, container_files_base_path, container: Cube
    ):
        super().__init__(container_config_parser, container_files_base_path)
        self.container = container
        self._ca = None

        self._encrypted_image_path = (
            None  # Set in download_encrypted_image_file; file deleted in decrypt_image
        )
        self._decrypted_image_path = (
            None  # Set in download_encrypted_image_file; file created in decrypt
        )

    @property
    def ca(self):
        if self._ca is None:
            try:
                self._ca = CA.from_container(self.container.id)
            except CommunicationRetrievalError:
                error_msg = (
                    f"No associated Certificate Authority (CA) was found for the Container {self.container.name} (UID: {self.container.id})\n"
                    f"If you are the Model Owner responsible for this container, please run the following command to create the association:\n"
                    f"medperf container associate_with_ca --container-id {self.container.id} --ca-id <ID of your preferred CA here>"
                )
                raise CommunicationRetrievalError(error_msg)
        return self._ca

    def download(
        self,
        expected_image_hash,
        download_timeout: int = None,
        get_hash_timeout: int = None,
        alternative_image_hash: str = None,
    ):
        """This can be either a docker archive tar file or an encrypted singularity .sif file"""
        encrypted_file_url = self.parser.get_setup_args()
        encrypted_file_path, computed_hash = resources.get_cube_image(
            encrypted_file_url, expected_image_hash
        )
        self._encrypted_image_path = encrypted_file_path
        self._decrypted_image_path = f"{self._encrypted_image_path}_decrypted"

        return computed_hash

    def _decrypt_image(self) -> str:
        """Decrypts downloaded encrypted image"""
        decryptor = self._load_symmetric_decryptor()

        with (
            open(self._encrypted_image_path, "rb") as encrypted_f,
            open(self._decrypted_image_path, "wb") as decrypted_f,
        ):
            decrypted_bytes = decryptor.decrypt(encrypted_f.read())
            decrypted_f.write(decrypted_bytes)

        return self._decrypted_image_path

    def _load_symmetric_decryptor(self) -> Fernet:
        container_key_dir = get_container_key_dir_path(
            container_id=self.container.id, ca_name=self.ca.name
        )

        model_owner_key_path = os.path.join(
            container_key_dir,
            config.container_key_file,
        )

        if os.path.exists(model_owner_key_path):
            with open(model_owner_key_path, "rb") as f:
                decrypted_key = f.read()

        else:
            # TODO request to server to download encrypted key
            private_key_info = load_private_key_info(
                ca=self.ca, container=self.container
            )

            data_owner_key_path = os.path.join(
                container_key_dir, config.encrypted_container_key_file
            )
            encrypted_symmetric_key = load_encrypted_symmetric_key_and_delete(
                data_owner_key_path
            )
            decrypted_key = private_key_info.private_key.decrypt(
                ciphertext=encrypted_symmetric_key,
                padding=private_key_info.padding,
            )

        fernet_obj = Fernet(decrypted_key)
        return fernet_obj

    @staticmethod
    def _safe_remove_file(file_path: Union[str, None]):
        """
        Removes the file indicated by `filepath`.
        If the file does not exist (already cleaned up) or if file_path is None
        (ie file_path is something that was not set up before cleanup)
        then this does nothing.
        """
        try:
            remove_path(file_path)
        except (AttributeError, FileNotFoundError):
            pass

    @abstractmethod
    def clean_up(self, *args):
        """
        Cleaning of assets after running
        This will clean up possible leftover images, but each implementation
        should also have a specific method for cleanup (for example, docker needs to delete
        the image and container from the daemon)
        """
        self._safe_remove_file(self._encrypted_image_path)
        self._safe_remove_file(self._decrypted_image_path)
