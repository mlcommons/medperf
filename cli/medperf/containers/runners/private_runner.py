from .decryption_utils import (
    SymmetricKeyFiles,
    decrypt_image,
    load_private_key_info,
    load_encrypted_symmetric_key_info,
    get_encrypted_symmetric_key_files,
)
from .runner import Runner
from medperf.comms.entity_resources import resources
from medperf.utils import get_pki_assets_path, remove_path
from medperf import config
import os
from abc import abstractmethod


class PrivateRunner(Runner):
    def __init__(self, container_config_parser, container_files_base_path):
        super().__init__(container_config_parser, container_files_base_path)
        self._encrypted_image_path = (
            None  # Set in download_encrypted_image_file; file deleted in decrypt_image
        )
        self._decrypted_image_path = (
            None  # Set in download_encrypted_image_file; file created in decrypt
        )
        # TODO clarify when we load these files in
        self._encrypted_symmetric_key_files: SymmetricKeyFiles = (
            None  # set in decrypt, files deleted after use
        )

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

    def decrypt_image(self) -> str:
        """Decrypts downloaded encrypted image"""

        self._encrypted_symmetric_key_files = get_encrypted_symmetric_key_files()
        encrypted_symmetric_key_info = load_encrypted_symmetric_key_info(
            encrypted_key_file_path=self._encrypted_symmetric_key_files.encrypted_key_file,
            nonce_file_path=self._encrypted_symmetric_key_files.nonce_file,
            tag_file_path=self._encrypted_symmetric_key_files.tag_file,
        )
        self._encrypted_symmetric_key_files.delete_files()

        # TODO pass this information into Runner or Parser
        pki_assets_path = get_pki_assets_path(common_name="test", ca_name="test")
        private_key_path = os.path.join(pki_assets_path, config.private_key_file)
        private_key_info = load_private_key_info(private_key_path=private_key_path)

        decrypted_image_path = decrypt_image(
            encrypted_symmetric_key_info=encrypted_symmetric_key_info,
            private_key_info=private_key_info,
            encrypted_image_path=self._encrypted_image_path,
            decrypted_image_path=self._decrypted_image_path,
        )

        remove_path(self._encrypted_image_path)

        return decrypted_image_path

    @abstractmethod
    def clean_up(self, *args):
        """
        Cleaning of assets after running
        This will clean up possible leftover images, but each implementation
        should also have a specific method for cleanup (for example, docker needs to delete
        the image and container from the daemon)
        """
        try:
            self._encrypted_symmetric_key_files.delete_files()
        except AttributeError:
            pass

        try:
            remove_path(self._encrypted_image_path)
        except (TypeError, FileNotFoundError):
            pass

        try:
            remove_path(self._decrypted_image_path)
        except (TypeError, FileNotFoundError):
            pass
