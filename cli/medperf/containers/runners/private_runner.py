from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Union
import os
from cryptography.fernet import Fernet, InvalidToken

from .runner import Runner
from .decryption_utils import load_private_key

from medperf import config
from medperf.comms.entity_resources import resources
from medperf.entities.ca import CA
from medperf.exceptions import (
    CommunicationRetrievalError,
    MissingContainerKeyException,
    DecryptionError,
    AuthenticationError
)
from medperf.utils import remove_path, get_container_key_dir_path
from medperf.entities.encrypted_container_key import EncryptedContainerKey
from medperf.account_management.account_management import get_medperf_user_data

if TYPE_CHECKING:
    from medperf.entities.cube import Cube


class PrivateRunner(Runner):
    def __init__(
        self, container_config_parser, container_files_base_path, container: Cube
    ):
        super().__init__(container_config_parser, container_files_base_path)
        self.container = container
        self._decryption_key = container.decryption_key
        self._ca = None

        self._encrypted_image_path = (
            None  # Set in download_encrypted_image_file; file deleted in decrypt_image
        )
        self._decrypted_image_path = (
            None  # Set in download_encrypted_image_file; file created in decrypt
        )
        self._must_delete_encrypted_image = self._check_if_must_delete_encrypted_image()

    @property
    def ca(self):
        if self._ca is None:
            try:
                self._ca = CA.from_container(self.container.id)
            except CommunicationRetrievalError:
                error_msg = (
                    f"No associated Certificate Authority (CA) was found "
                    f"for the Container {self.container.name} (UID: {self.container.id})\n"
                    f"If you are the Model Owner responsible for this container, "
                    f"please run the following command to create the association:\n"
                    f"medperf container associate_with_ca --container-id {self.container.id} "
                    "--decryption-key <path to your decryption key file> "
                    "--ca-id <ID of your preferred CA here>"
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

        try:
            with (
                open(self._encrypted_image_path, "rb") as encrypted_f,
                open(self._decrypted_image_path, "wb") as decrypted_f,
            ):
                decrypted_bytes = decryptor.decrypt(encrypted_f.read())
                decrypted_f.write(decrypted_bytes)
        except InvalidToken:
            raise DecryptionError(
                f"Error when decrypting Container {self.container.id}. Try redownloading the Container."
            )
        return self._decrypted_image_path

    def _load_symmetric_decryptor(self) -> Fernet:
        if self._decryption_key is not None:
            return Fernet(self._decryption_key)

        container_key_dir = get_container_key_dir_path(
            container_id=self.container.id, ca_name=self.ca.name
        )

        model_owner_key_path = os.path.join(
            container_key_dir,
            config.container_key_file,
        )

        if self._must_delete_encrypted_image:
            if os.path.exists(model_owner_key_path):
                decrypted_key = self._load_model_owner_local_key(model_owner_key_path)
            else:
                msg = (
                    f"Container Key not found for Container ID {self.container.id}.\n"
                    f"If attempting to execute a compatibility test run, please make "
                    "sure to include the --decryption-key option in your compatibility "
                    "test run command.\n"
                    f"If attempting to associate with a benchmark AND you are the Model "
                    "Owner responsible for this container, please run the following command "
                    "to create the association:\n"
                    f"medperf container associate_with_ca --container-id {self.container.id} "
                    "--decryption-key <path to your decryption key file> "
                    "--ca-id <ID of your preferred CA here>"
                )
                raise MissingContainerKeyException(msg)
        else:
            decrypted_key = self._load_data_owner_key()

        fernet_obj = Fernet(decrypted_key)
        return fernet_obj

    def _check_if_must_delete_encrypted_image(self) -> bool:
        """
        Keep encrypted image if current user is the model owner or if 
        execution is local (ie they already have the decrypted model 
        anyway). Delete encrypted image in all other scenarios, 
        including if we cannot verify the user identity.

        Decrypted image is always deleted after execution.
        """
        if self.container.is_local:
            return False
        else:
            try:
                current_user_id = get_medperf_user_data()["id"]
                model_owner_id = self.container.owner
                return current_user_id != model_owner_id
            except AuthenticationError:
                return True
    @staticmethod
    def _load_model_owner_local_key(model_owner_key_path: str) -> bytes:
        with open(model_owner_key_path, "rb") as f:
            decrypted_key = f.read()
        return decrypted_key

    def _load_data_owner_key(self) -> bytes:
        encrypted_key_obj = EncryptedContainerKey.get_from_model(self.container.id)
        private_key = load_private_key(ca=self.ca, container=self.container)

        decrypted_key = private_key.decrypt(
            ciphertext=encrypted_key_obj.encrypted_key,
            padding=encrypted_key_obj.padding,
        )

        return decrypted_key

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
        if self._must_delete_encrypted_image:
            self._safe_remove_file(self._encrypted_image_path)
        self._safe_remove_file(self._decrypted_image_path)
