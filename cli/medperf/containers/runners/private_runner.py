from .decryption_utils import (
    decrypt_image,
    load_private_key_info,
    load_encrypted_symmetric_key_info,
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
        encrypted_key_path = ""
        nonce_path = ""
        tag_path = ""

        encrypted_symmetric_key_info = load_encrypted_symmetric_key_info(
            encrypted_key_file_path=encrypted_key_path,
            nonce_file_path=nonce_path,
            tag_file_path=tag_path,
        )

        for asset in [encrypted_key_path, nonce_path, tag_path]:
            remove_path(asset)

        pki_assets_path = get_pki_assets_path()
        private_key_path = os.path.join(pki_assets_path, config.private_key_file)
        private_key_info = load_private_key_info(private_key_path=private_key_path)

        decrypted_image_file = decrypt_image(
            encrypted_symmetric_key_info=encrypted_symmetric_key_info,
            private_key_info=private_key_info,
            encrypted_image_path=self._encrypted_image_path,
            decrypted_image_path=self._decrypted_image_path,
        )

        remove_path(self._encrypted_image_path)

        return decrypted_image_file

    @abstractmethod
    def load_image(self, decrypted_image):
        """Loads decrypted image into Docker/Singularity/Other engine"""
        pass

    @abstractmethod
    def clean_up(self, *args):
        """
        Cleaning of assets after running
        This will clean up possible leftover images, but each implementation
        should also have a specific method for cleanup (for example, docker needs to delete
        the image and container from the daemon)
        """
        try:
            remove_path(self._encrypted_image_path)
        except FileNotFoundError:
            pass

        try:
            remove_path(self._decrypted_image_path)
        except FileNotFoundError:
            pass
