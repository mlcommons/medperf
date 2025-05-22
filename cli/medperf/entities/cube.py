import os
from typing import Optional, Union, List
from pydantic import Field
from medperf.entities.interface import Entity
from medperf.entities.schemas import DeployableSchema
from medperf.exceptions import InvalidEntityError
import medperf.config as config
from medperf.comms.entity_resources import resources
from medperf.account_management import get_medperf_user_data
from medperf.containers.runners import load_runner
from medperf.containers.parsers import load_parser


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
        return "container"

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
        self.additiona_files_folder_path = None
        self.params_path = os.path.join(
            self.path, config.workspace_path, config.params_filename
        )
        self.additiona_files_folder_path = os.path.join(
            self.path, config.additional_path
        )
        self._parser = None
        self._runner = None

    @property
    def parser(self):
        if self._parser is None:
            self._parser = load_parser(self.cube_path)
        return self._parser

    @property
    def runner(self):
        if self._runner is None:
            self._runner = load_runner(self.parser, self.path)
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
    def get(
        cls,
        cube_uid: Union[str, int],
        local_only: bool = False,
        valid_only: bool = True,
    ) -> "Cube":
        """Retrieves and creates a Cube instance from the comms. If cube already exists
        inside the user's computer then retrieves it from there.

        Args:
            valid_only: if to raise an error in case of invalidated Cube
            cube_uid (str): UID of the cube.

        Returns:
            Cube : a Cube instance with the retrieved data.
        """

        cube = super().get(cube_uid, local_only)
        if not cube.is_valid and valid_only:
            raise InvalidEntityError("The requested container is marked as INVALID.")
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
            path, file_hash = resources.get_cube_additional(
                url, self.path, self.additional_files_tarball_hash
            )
            self.additiona_files_folder_path = path
            self.additional_files_tarball_hash = file_hash

    def download_config_files(self):
        try:
            self.download_mlcube()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"Container {self.name} config file: {e}")

        try:
            self.download_parameters()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"Container {self.name} parameters file: {e}")

    def download_run_files(self):
        try:
            self.download_additional()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"Container {self.name} additional files: {e}")

        try:
            self.image_hash = self.runner.download(
                expected_image_hash=self.image_hash,
                download_timeout=config.mlcube_configure_timeout,
                get_hash_timeout=config.mlcube_inspect_timeout,
            )
        except InvalidEntityError as e:
            raise InvalidEntityError(f"Container {self.name} image: {e}")

    def run(
        self,
        task: str,
        output_logs: str = None,
        timeout: int = None,
        mounts: dict = {},
        env: dict = {},
        ports: list = [],
        disable_network: bool = True,
    ):
        os.makedirs(self.additiona_files_folder_path, exist_ok=True)
        extra_mounts = {
            "parameters_file": self.params_path,
            "additional_files": self.additiona_files_folder_path,
        }

        extra_env = {}
        if config.container_loglevel is not None:
            extra_env["MEDPERF_LOGLEVEL"] = config.container_loglevel.upper()

        self.runner.run(
            task,
            output_logs,
            timeout,
            medperf_mounts={**mounts, **extra_mounts},
            medperf_env={**env, **extra_env},
            ports=ports,
            disable_network=disable_network,
        )

    def is_report_specified(self):
        return self.parser.is_report_specified()

    def is_metadata_specified(self):
        return self.parser.is_metadata_specified()

    @classmethod
    def get_benchmarks_associations(cls, mlcube_uid: int) -> List[Association]:
        """Retrieves the list of benchmarks model is associated with

        Args:
            mlcube_uid (int): UID of the cube.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[Association]: List of associations
        """
        associations = config.comms.get_cubes_associations()
        associations = [Association(**assoc) for assoc in associations]
        associations = [a for a in associations if a.model_mlcube == mlcube_uid]
        return associations

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Config File": self.git_mlcube_url,
            "State": self.state,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
