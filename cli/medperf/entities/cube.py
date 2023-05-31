import os
import yaml
import pexpect
import logging
from deepdiff import DeepDiff
from typing import List, Dict, Optional, Union
from pydantic import Field
from pathlib import Path

from medperf.utils import combine_proc_sp_text, list_files, storage_path
from medperf.entities.interface import Entity, Updatable
from medperf.entities.schemas import MedperfSchema, DeployableSchema
from medperf.exceptions import (
    InvalidArgumentError,
    ExecutionError,
    InvalidEntityError,
    MedperfException,
    CommunicationRetrievalError,
)
import medperf.config as config
from medperf.comms.entity_resources import resources


class Cube(Entity, Updatable, MedperfSchema, DeployableSchema):
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
    additional_files_tarball_url: Optional[str] = Field(None, alias="tarball_url")
    additional_files_tarball_hash: Optional[str] = Field(None, alias="tarball_hash")
    metadata: dict = {}
    user_metadata: dict = {}

    def __init__(self, *args, **kwargs):
        """Creates a Cube instance

        Args:
            cube_desc (Union[dict, CubeModel]): MLCube Instance description
        """
        super().__init__(*args, **kwargs)

        self.generated_uid = self.name
        path = storage_path(config.cubes_storage)
        if self.id:
            path = os.path.join(path, str(self.id))
        else:
            path = os.path.join(path, self.generated_uid)
        # NOTE: maybe have these as @property, to have the same entity reusable
        #       before and after submission
        self.path = path
        self.cube_path = os.path.join(path, config.cube_filename)
        self.params_path = None
        if self.git_parameters_url:
            self.params_path = os.path.join(path, config.params_filename)

    @classmethod
    def all(cls, local_only: bool = False, filters: dict = {}) -> List["Cube"]:
        """Class method for retrieving all retrievable MLCubes

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            filters (dict, optional): key-value pairs specifying filters to apply to the list of entities.

        Returns:
            List[Cube]: List containing all cubes
        """
        logging.info("Retrieving all cubes")
        cubes = []
        if not local_only:
            cubes = cls.__remote_all(filters=filters)

        remote_uids = set([cube.id for cube in cubes])

        local_cubes = cls.__local_all()

        cubes += [cube for cube in local_cubes if cube.id not in remote_uids]

        return cubes

    @classmethod
    def __remote_all(cls, filters: dict) -> List["Cube"]:
        cubes = []

        try:
            comms_fn = cls.__remote_prefilter(filters)
            cubes_meta = comms_fn()
            cubes = [cls(**meta) for meta in cubes_meta]
        except CommunicationRetrievalError:
            msg = "Couldn't retrieve all cubes from the server"
            logging.warning(msg)

        return cubes

    @classmethod
    def __remote_prefilter(cls, filters: dict):
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_cubes
        if "owner" in filters and filters["owner"] == config.current_user["id"]:
            comms_fn = config.comms.get_user_cubes

        return comms_fn

    @classmethod
    def __local_all(cls) -> List["Cube"]:
        cubes = []
        cubes_storage = storage_path(config.cubes_storage)
        try:
            uids = next(os.walk(cubes_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over cubes directory"
            logging.warning(msg)
            raise MedperfException(msg)

        for uid in uids:
            meta = cls.__get_local_dict(uid)
            cube = cls(**meta)
            cubes.append(cube)

        return cubes

    @classmethod
    def get(cls, cube_uid: Union[str, int], local_only: bool = False) -> "Cube":
        """Retrieves and creates a Cube instance from the comms. If cube already exists
        inside the user's computer then retrieves it from there.

        Args:
            cube_uid (str): UID of the cube.

        Returns:
            Cube : a Cube instance with the retrieved data.
        """

        if not str(cube_uid).isdigit() or local_only:
            cube = cls.__local_get(cube_uid)
        else:
            try:
                cube = cls.__remote_get(cube_uid)
            except CommunicationRetrievalError:
                logging.warning(f"Getting MLCube {cube_uid} from comms failed")
                logging.info(f"Retrieving MLCube {cube_uid} from local storage")
                cube = cls.__local_get(cube_uid)

        if not cube.is_valid:
            raise InvalidEntityError("The requested MLCube is marked as INVALID.")
        cube.download()
        return cube

    @classmethod
    def __remote_get(cls, cube_uid: int) -> "Cube":
        logging.debug(f"Retrieving mlcube {cube_uid} remotely")
        meta = config.comms.get_cube_metadata(cube_uid)
        cube = cls(**meta)
        cube.write()
        return cube

    @classmethod
    def __local_get(cls, cube_uid: Union[str, int]) -> "Cube":
        logging.debug(f"Retrieving cube {cube_uid} locally")
        local_meta = cls.__get_local_dict(cube_uid)
        cube = cls(**local_meta)
        return cube

    def download_mlcube(self, force=False):
        url = self.git_mlcube_url
        path, file_hash = resources.get_cube(
            url, self.path, self.mlcube_hash, force=force
        )
        self.cube_path = path
        self.mlcube_hash = file_hash

    def download_parameters(self, force=False):
        url = self.git_parameters_url
        if url:
            path, file_hash = resources.get_cube_params(
                url, self.path, self.parameters_hash, force=force
            )
            self.params_path = path
            self.parameters_hash = file_hash

    def download_additional(self, force=False):
        url = self.additional_files_tarball_url
        if url:
            file_hash = resources.get_cube_additional(
                url, self.path, self.additional_files_tarball_hash, force=force
            )
            self.additional_files_tarball_hash = file_hash

    def download_image(self, force=False):
        url = self.image_tarball_url
        hash = self.image_tarball_hash

        if url:
            _, local_hash = resources.get_cube_image(url, self.path, hash, force=force)
            self.image_tarball_hash = local_hash
        else:
            # Retrieve image from image registry
            logging.debug(f"Retrieving {self.id} image")
            cmd = f"mlcube configure --mlcube={self.cube_path}"
            proc = pexpect.spawn(cmd)
            proc_out = combine_proc_sp_text(proc)
            logging.debug(proc_out)
            proc.close()

    def download(self):
        """Downloads the required elements for an mlcube to run locally."""
        try:
            self.download_mlcube()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} manifest file: {e}")

        try:
            self.download_parameters()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} parameters file: {e}")

        try:
            self.download_additional()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} additional files: {e}")

        try:
            self.download_image()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} image file: {e}")

    def run(
        self,
        task: str,
        string_params: Dict[str, str] = {},
        timeout: int = None,
        **kwargs,
    ):
        """Executes a given task on the cube instance

        Args:
            task (str): task to run
            string_params (Dict[str], optional): Extra parameters that can't be passed as normal function args.
                                                 Defaults to {}.
            timeout (int, optional): timeout for the task in seconds. Defaults to None.
            kwargs (dict): additional arguments that are passed directly to the mlcube command
        """
        kwargs.update(string_params)
        cmd = f"mlcube run --mlcube={self.cube_path} --task={task} --platform={config.platform}"
        for k, v in kwargs.items():
            cmd_arg = f'{k}="{v}"'
            cmd = " ".join([cmd, cmd_arg])
        logging.info(f"Running MLCube command: {cmd}")
        proc = pexpect.spawn(cmd, timeout=timeout)
        proc_out = combine_proc_sp_text(proc)
        proc.close()
        logging.debug(proc_out)
        if proc.exitstatus != 0:
            raise ExecutionError("There was an error while executing the cube")

        logging.debug(list_files(config.storage))
        return proc

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
        with open(self.cube_path, "r") as f:
            cube = yaml.safe_load(f)

        out_params = cube["tasks"][task]["parameters"]["outputs"]
        if out_key not in out_params:
            return None

        out_path = cube["tasks"][task]["parameters"]["outputs"][out_key]
        if type(out_path) == dict:
            # output is specified as a dict with type and default values
            out_path = out_path["default"]
        cube_loc = str(Path(self.cube_path).parent)
        out_path = os.path.join(cube_loc, "workspace", out_path)

        if self.params_path is not None and param_key is not None:
            with open(self.params_path, "r") as f:
                params = yaml.safe_load(f)

            out_path = os.path.join(out_path, params[param_key])

        return out_path

    def edit(self, **kwargs):
        """Edits a cube with the given property-value pairs"""
        data = self.todict()

        # Include the updated fields
        data.update(kwargs)
        new_cube = Cube(**data)

        # If any resource is being updated, download and get the new hash
        # Hash difference checking is done between the old and new cube
        # According to update policies
        if "git_mlcube_url" in kwargs:
            new_cube.mlcube_hash = kwargs.get("mlcube_hash", None)
            new_cube.download_mlcube(force=True)
        if "git_parameters_url" in kwargs:
            new_cube.parameters_hash = kwargs.get("parameters_hash", None)
            new_cube.download_parameters(force=True)
        if "image_tarball_url" in kwargs:
            new_cube.image_tarball_hash = kwargs.get("image_tarball_hash", None)
            new_cube.download_image(force=True)
        if "additional_files_tarball_url" in kwargs:
            new_cube.additional_files_tarball_hash = kwargs.get(
                "additional_files_tarball_hash", None
            )
            new_cube.download_additional(force=True)

        self.__validate_edit(new_cube)

        self.__dict__.update(**new_cube.__dict__)

    def __validate_edit(self, new_cube: "Cube"):
        """Ensure an edit is valid given the changes made

        Args:
            new_cube (Cube): The new version of the same MLCube

        Raises:
            InvalidEntityError: The changes created an invalid entity configuration
            InvalidArugmentError: The changed fields are not mutable
        """
        old_cube = self
        # Fields that shouldn't be modified directly by the user
        inmutable_fields = {
            "id",
        }

        # Fields that can no longer be modified while in production
        production_inmutable_fields = {
            "mlcube_hash",
            "parameters_hash",
            "image_tarball_hash",
            "additional_files_tarball_hash",
        }

        if old_cube.state == "OPERATION":
            inmutable_fields = inmutable_fields.union(production_inmutable_fields)

        cube_diffs = DeepDiff(new_cube.todict(), old_cube.todict())
        updated_fields = set(cube_diffs.affected_root_keys)

        updated_inmutable_fields = updated_fields.intersection(inmutable_fields)

        if len(updated_inmutable_fields):
            fields_msg = ", ".join(updated_inmutable_fields)
            msg = (
                "The following fields can't be directly edited: "
                + fields_msg
                + ". For these changes, a new MLCube is required"
            )
            raise InvalidArgumentError(msg)

    def update(self):
        """Updates the benchmark on the server"""
        if not self.is_registered:
            raise MedperfException("Can't update an unregistered cube")
        body = self.todict()
        config.comms.update_mlcube(self.id, body)

    def todict(self) -> Dict:
        return self.extended_dict()

    def write(self):
        cube_loc = str(Path(self.cube_path).parent)
        meta_file = os.path.join(cube_loc, config.cube_metadata_filename)
        os.makedirs(cube_loc, exist_ok=True)
        with open(meta_file, "w") as f:
            yaml.dump(self.todict(), f)
        return meta_file

    def upload(self):
        if self.for_test:
            raise InvalidArgumentError("Cannot upload test mlcubes.")
        cube_dict = self.todict()
        updated_cube_dict = config.comms.upload_mlcube(cube_dict)
        return updated_cube_dict

    @classmethod
    def __get_local_dict(cls, uid):
        cubes_storage = storage_path(config.cubes_storage)
        meta_file = os.path.join(cubes_storage, str(uid), config.cube_metadata_filename)
        if not os.path.exists(meta_file):
            raise InvalidArgumentError(
                "The requested mlcube information could not be found locally"
            )
        with open(meta_file, "r") as f:
            meta = yaml.safe_load(f)
        return meta

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Config File": self.git_mlcube_url,
            "State": self.state,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
