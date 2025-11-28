import os

import medperf.config as config
from medperf.entities.cube import Cube
from medperf.exceptions import InvalidArgumentError
from medperf.utils import remove_path, sanitize_path, store_decryption_key
import logging


class SubmitCube:
    @classmethod
    def run(cls, submit_info: dict, decryption_key: str = None):
        """Submits a new cube to the medperf platform

        Args:
            submit_info (dict): Dictionary containing the cube information.
        """
        ui = config.ui
        submission = cls(submit_info, decryption_key)
        with ui.interactive():
            ui.text = "Validating Container can be downloaded"
            submission.download_config_files()
            submission.validate()
            submission.download_run_files()
            ui.text = "Submitting Container to MedPerf"
            updated_cube_dict = submission.upload()
            submission.to_permanent_path(updated_cube_dict)
            submission.write(updated_cube_dict)
            submission.store_decryption_key()
        return submission.cube.id

    def __init__(self, submit_info: dict, decryption_key: str = None):
        self.comms = config.comms
        self.ui = config.ui
        self.cube = Cube(**submit_info)
        self.decryption_key = sanitize_path(decryption_key)
        config.tmp_paths.append(self.cube.path)

    def download_config_files(self):
        self.cube.download_config_files()

    def validate(self):
        if self.cube.is_encrypted() and not self.decryption_key:
            raise InvalidArgumentError(
                "Container seems to be encrypted, but no decryption key is provided"
            )

        if not self.cube.is_encrypted() and self.decryption_key:
            raise InvalidArgumentError(
                "Container is not encrypted, but a decryption key is provided"
            )

        if self.decryption_key is not None:
            if not os.path.exists(self.decryption_key):
                raise InvalidArgumentError(
                    f"Decryption key does not exist at path {self.decryption_key}"
                )
            if os.path.isdir(self.decryption_key):
                raise InvalidArgumentError(
                    f"The provided decryption key path {self.decryption_key} is a directory!"
                )

    def download_run_files(self):
        self.cube.download_run_files()

    def upload(self):
        updated_body = self.cube.upload()
        return updated_body

    def to_permanent_path(self, cube_dict):
        """Renames the temporary cube submission to a permanent one using the uid of
        the registered cube
        """
        old_cube_loc = self.cube.path
        updated_cube = Cube(**cube_dict)
        new_cube_loc = updated_cube.path
        remove_path(new_cube_loc)
        os.rename(old_cube_loc, new_cube_loc)

    def write(self, updated_cube_dict):
        self.cube = Cube(**updated_cube_dict)
        self.cube.write()

    def store_decryption_key(self):
        if self.decryption_key is None:
            logging.debug("Decryption key not provided")
            return
        logging.debug(f"Decryption key provided: {self.decryption_key}")
        store_decryption_key(self.cube.id, self.decryption_key)
