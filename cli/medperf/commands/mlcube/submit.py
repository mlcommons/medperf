import os
from typing import Optional
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.exceptions import InvalidArgumentError
from medperf.utils import remove_path, store_decryption_key, sanitize_path
import logging

import yaml


class SubmitCube:
    @classmethod
    def run(
        cls,
        submit_info: dict,
        container_config: str,
        parameters_config: Optional[str] = None,
        decryption_key: str = None,
    ):
        """Submits a new cube to the medperf platform

        Args:
            submit_info (dict): Dictionary containing the cube information.
        """
        ui = config.ui
        submission = cls(
            submit_info, container_config, parameters_config, decryption_key
        )
        submission.read_config_files()
        submission.create_cube_object()

        with ui.interactive():
            ui.text = "Validating Container can be downloaded"
            submission.validate()
            submission.download_run_files()
            ui.text = "Submitting Container to MedPerf"
            updated_cube_dict = submission.upload()
            submission.to_permanent_path(updated_cube_dict)
            submission.write(updated_cube_dict)
            submission.store_decryption_key()
        return submission.cube.id

    def __init__(
        self,
        submit_info: dict,
        container_config: str,
        parameters_config: Optional[str] = None,
        decryption_key: str = None,
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.submit_info = submit_info
        self.container_config_file = sanitize_path(container_config)
        self.parameters_config_file = sanitize_path(parameters_config)
        self.container_config = None
        self.parameters_config = None
        self.decryption_key = decryption_key

    def read_config_files(self):
        if not os.path.exists(self.container_config_file):
            raise InvalidArgumentError(
                f"Container config file {self.container_config_file} does not exist"
            )
        if not os.path.isfile(self.container_config_file):
            raise InvalidArgumentError(
                f"Container config file {self.container_config_file} is not a file"
            )

        if self.parameters_config_file:
            if not os.path.exists(self.parameters_config_file):
                raise InvalidArgumentError(
                    f"Parameters config file {self.parameters_config_file} does not exist"
                )
            if not os.path.isfile(self.parameters_config_file):
                raise InvalidArgumentError(
                    f"Parameters config file {self.parameters_config_file} is not a file"
                )

        with open(self.container_config_file, "r") as f:
            container_config_content = yaml.safe_load(f)
        if container_config_content is None:
            raise InvalidArgumentError(
                f"Container config file {self.container_config_file} is empty"
            )

        parameters_config_content = None
        if self.parameters_config_file:
            with open(self.parameters_config_file, "r") as f:
                parameters_config_content = yaml.safe_load(f)
            if parameters_config_content is None:
                parameters_config_content = dict()

        self.container_config = container_config_content
        self.parameters_config = parameters_config_content

    def create_cube_object(self):
        self.cube = Cube(
            **self.submit_info,
            container_config=self.container_config,
            parameters=self.parameters_config,
        )
        config.tmp_paths.append(self.cube.path)

    def validate(self):
        if self.cube.is_encrypted() and not self.decryption_key:
            raise InvalidArgumentError(
                "Container seems to be encrypted, but no decryption key is provided"
            )

        if not self.cube.is_encrypted() and self.decryption_key:
            raise InvalidArgumentError(
                "Container is not encrypted, but a decryption key is provided"
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
