import os
import yaml
import logging
from typing import Dict, Optional, Union
from pydantic import Field
from pathlib import Path

from medperf.utils import (
    combine_proc_sp_text,
    log_storage,
    remove_path,
    generate_tmp_path,
    spawn_and_kill,
)
from medperf.entities.interface import Entity
from medperf.entities.schemas import DeployableSchema
from medperf.exceptions import InvalidArgumentError, ExecutionError, InvalidEntityError
import medperf.config as config
from medperf.comms.entity_resources import resources
from medperf.account_management import get_medperf_user_data
from medperf.containers.container import load_runner


class Cube(Entity, DeployableSchema):
    """
    Class representing an MLCube Container

    Medperf platform uses the MLCube container for components such as
    Dataset Preparation, Evaluation, and the Registered Models. MLCube
    containers are software containers (e.g., Docker and Singularity)
    with standard metadata and a consistent file-system level interface.
    """

    git_mlcube_url: str
    mlcube_hash: Optional[str]
    git_parameters_url: Optional[str]
    parameters_hash: Optional[str]
    image_tarball_url: Optional[str]
    image_tarball_hash: Optional[str]
    image_hash: Optional[str]
    additional_files_tarball_url: Optional[str] = Field(None, alias="tarball_url")
    additional_files_tarball_hash: Optional[str] = Field(None, alias="tarball_hash")
    metadata: dict = {}
    user_metadata: dict = {}

    @staticmethod
    def get_type():
        return "cube"

    @staticmethod
    def get_storage_path():
        return config.cubes_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_cube_metadata

    @staticmethod
    def get_metadata_filename():
        return config.cube_metadata_filename

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_mlcube

    def __init__(self, *args, **kwargs):
        """Creates a Cube instance

        Args:
            cube_desc (Union[dict, CubeModel]): MLCube Instance description
        """
        super().__init__(*args, **kwargs)

        self.cube_path = os.path.join(self.path, config.cube_filename)
        self.params_path = None
        if self.git_parameters_url:
            self.params_path = os.path.join(self.path, config.params_filename)
        self._runner = None

    @property
    def runner(self):
        if self._runner is None:
            return load_runner(self.cube_path)
        return self._runner

    @property
    def local_id(self):
        return self.name

    @staticmethod
    def remote_prefilter(filters: dict):
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_cubes
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_cubes

        return comms_fn

    @classmethod
    def get(cls, cube_uid: Union[str, int], local_only: bool = False) -> "Cube":
        """Retrieves and creates a Cube instance from the comms. If cube already exists
        inside the user's computer then retrieves it from there.

        Args:
            cube_uid (str): UID of the cube.

        Returns:
            Cube : a Cube instance with the retrieved data.
        """

        cube = super().get(cube_uid, local_only)
        if not cube.is_valid:
            raise InvalidEntityError("The requested MLCube is marked as INVALID.")
        cube.download_config_files()
        return cube

    def download_mlcube(self):
        url = self.git_mlcube_url
        path, file_hash = resources.get_cube(url, self.path, self.mlcube_hash)
        self.cube_path = path
        self.mlcube_hash = file_hash

    def download_parameters(self):
        url = self.git_parameters_url
        if url:
            path, file_hash = resources.get_cube_params(
                url, self.path, self.parameters_hash
            )
            self.params_path = path
            self.parameters_hash = file_hash

    def download_additional(self):
        url = self.additional_files_tarball_url
        if url:
            file_hash = resources.get_cube_additional(
                url, self.path, self.additional_files_tarball_hash
            )
            self.additional_files_tarball_hash = file_hash

    @property
    def _converted_singularity_image_name(self):
        return f"{self.image_hash}.sif"

    def download_config_files(self):
        try:
            self.download_mlcube()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} manifest file: {e}")

        try:
            self.download_parameters()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} parameters file: {e}")

    def download_run_files(self):
        try:
            self.download_additional()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} additional files: {e}")

        try:
            self.image_hash = self.runner.download()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} image file: {e}")

    def run(
        self,
        task: str,
        output_logs: str = None,
        timeout: int = None,
        **kwargs,
    ):
        self.runner.run(task, output_logs, timeout, kwargs)

    def get_default_output(self, task: str, out_key: str, param_key: str = None) -> str:
        """Returns the output parameter specified in the mlcube.yaml file

        Args:
            task (str): the task of interest
            out_key (str): key used to identify the desired output in the yaml file
            param_key (str): key inside the parameters file that completes the output path. Defaults to None.

        Returns:
            str: the path as specified in the mlcube.yaml file for the desired
                output for the desired task. Defaults to None if out_key not found
        """
        out_path = self.get_config(f"tasks.{task}.parameters.outputs.{out_key}")
        if out_path is None:
            return

        if isinstance(out_path, dict):
            # output is specified as a dict with type and default values
            out_path = out_path["default"]
        cube_loc = str(Path(self.cube_path).parent)
        out_path = os.path.join(cube_loc, "workspace", out_path)

        if self.params_path is not None and param_key is not None:
            with open(self.params_path, "r") as f:
                params = yaml.safe_load(f)

            out_path = os.path.join(out_path, params[param_key])

        return out_path

    def get_config(self, identifier):
        """
        Returns the output parameter specified in the mlcube.yaml file

        Args:
            identifier (str): `.` separated keys to traverse the mlcube dict
        Returns:
            str: the parameter value, None if not found
        """
        with open(self.cube_path, "r") as f:
            cube = yaml.safe_load(f)

        keys = identifier.split(".")
        for key in keys:
            if key not in cube:
                return
            cube = cube[key]

        return cube

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Config File": self.git_mlcube_url,
            "State": self.state,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
