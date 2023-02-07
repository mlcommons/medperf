import os
import sys
import yaml
import logging
from typing import List, Dict
from pathlib import Path

if sys.platform == "win32":
    from wexpect import spawn
else:
    from pexpect import spawn

from medperf.utils import (
    get_file_sha1,
    untar,
    combine_proc_sp_text,
    list_files,
    storage_path,
    cleanup,
)
from medperf.entities.interface import Entity
from medperf.exceptions import (
    InvalidArgumentError,
    ExecutionError,
    InvalidEntityError,
    MedperfException,
    CommunicationRetrievalError,
)
import medperf.config as config


class Cube(Entity):
    """
    Class representing an MLCube Container

    Medperf platform uses the MLCube container for components such as
    Dataset Preparation, Evaluation, and the Registered Models. MLCube
    containers are software containers (e.g., Docker and Singularity)
    with standard metadata and a consistent file-system level interface.
    """

    def __init__(self, cube_dict):
        """Creates a Cube instance

        Args:
            cube_dict (dict): Dict for information regarding the cube.

        """
        self.uid = cube_dict["id"]
        self.name = cube_dict["name"]
        self.git_mlcube_url = cube_dict["git_mlcube_url"]
        self.git_parameters_url = cube_dict["git_parameters_url"]
        self.mlcube_hash = cube_dict["mlcube_hash"]
        self.parameters_hash = cube_dict["parameters_hash"]
        self.image_tarball_url = cube_dict["image_tarball_url"]
        self.image_tarball_hash = cube_dict["image_tarball_hash"]
        if "tarball_url" in cube_dict:
            # Backwards compatibility for cubes with
            # tarball_url instead of additional_files_tarball_url
            self.additional_files_tarball_url = cube_dict["tarball_url"]
        else:
            self.additional_files_tarball_url = cube_dict[
                "additional_files_tarball_url"
            ]

        if "tarball_hash" in cube_dict:
            # Backwards compatibility for cubes with
            # tarball_hash instead of additional_files_tarball_hash
            self.additional_hash = cube_dict["tarball_hash"]
        else:
            self.additional_hash = cube_dict["additional_files_tarball_hash"]

        self.state = cube_dict["state"]
        self.is_cube_valid = cube_dict["is_valid"]
        self.owner = cube_dict["owner"]
        self.metadata = cube_dict["metadata"]
        self.user_metadata = cube_dict["user_metadata"]
        self.created_at = cube_dict["created_at"]
        self.modified_at = cube_dict["modified_at"]

        cubes_storage = storage_path(config.cubes_storage)
        self.cube_path = os.path.join(
            cubes_storage, str(self.uid), config.cube_filename
        )
        self.params_path = None
        if self.git_parameters_url:
            self.params_path = os.path.join(
                cubes_storage, str(self.uid), config.params_filename
            )

        self.generated_uid = self.name
        path = storage_path(config.cubes_storage)
        if self.uid:
            path = os.path.join(path, str(self.uid))
        else:
            path = os.path.join(path, str(self.generated_uid))

        self.path = path

    @classmethod
    def all(cls, local_only: bool = False, mine_only: bool = False) -> List["Cube"]:
        """Class method for retrieving all retrievable MLCubes

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            mine_only (bool, optional): Wether to retrieve only current-user entities.Defaults to False.

        Returns:
            List[Cube]: List containing all cubes
        """
        logging.info("Retrieving all cubes")
        cubes = []
        if not local_only:
            cubes = cls.__remote_all(mine_only=mine_only)

        remote_uids = set([cube.uid for cube in cubes])

        local_cubes = cls.__local_all()

        cubes += [cube for cube in local_cubes if cube.uid not in remote_uids]

        return cubes

    @classmethod
    def __remote_all(cls, mine_only: bool = False) -> List["Cube"]:
        cubes = []
        remote_func = config.comms.get_cubes
        if mine_only:
            remote_func = config.comms.get_user_cubes

        try:
            cubes_meta = remote_func()
            cubes = [cls(meta) for meta in cubes_meta]
        except CommunicationRetrievalError:
            msg = "Couldn't retrieve all cubes from the server"
            logging.warning(msg)

        return cubes

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
            cube = cls(meta)
            cubes.append(cube)

        return cubes

    @classmethod
    def get(cls, cube_uid: str) -> "Cube":
        """Retrieves and creates a Cube instance from the comms. If cube already exists
        inside the user's computer then retrieves it from there.

        Args:
            cube_uid (str): UID of the cube.

        Returns:
            Cube : a Cube instance with the retrieved data.
        """
        logging.debug(f"Retrieving the cube {cube_uid}")
        comms = config.comms

        # Try to download the cube first
        try:
            meta = comms.get_cube_metadata(cube_uid)
            cube = cls(meta)
            attempt = 0
            while attempt < config.cube_get_max_attempts:
                logging.info(f"Downloading MLCube. Attempt {attempt + 1}")
                # Check first if we already have the required files
                if cube.is_valid():
                    cube.write()
                    return cube
                # Try to redownload elements if invalid
                cube.download()
                attempt += 1
            cube.write()
        except CommunicationRetrievalError:
            logging.warning("Max download attempts reached")
            logging.warning(f"Getting MLCube {cube_uid} from comms failed")
            logging.info(f"Retrieving MLCube {cube_uid} from local storage")
            local_meta = cls.__get_local_dict(cube_uid)
            cube = cls(local_meta)
            return cube

        logging.error("Could not find the requested MLCube")
        cube_path = os.path.join(storage_path(config.cubes_storage), str(cube_uid))
        cleanup([cube_path])
        raise InvalidEntityError("Could not successfully get the requested MLCube")

    def download_mlcube(self):
        url = self.git_mlcube_url
        path = config.comms.get_cube(url, self.uid)
        local_hash = get_file_sha1(path)
        if not self.mlcube_hash:
            self.mlcube_hash = local_hash
        self.cube_path = path
        return local_hash

    def download_parameters(self):
        url = self.git_parameters_url
        if url:
            path = config.comms.get_cube_params(url, self.uid)
            local_hash = get_file_sha1(path)
            if not self.parameters_hash:
                self.parameters_hash = local_hash
            self.params_path = path
            return local_hash
        return ""

    def download_additional(self):
        url = self.additional_files_tarball_url
        if url:
            path = config.comms.get_cube_additional(url, self.uid)
            local_hash = get_file_sha1(path)
            if not self.additional_hash:
                self.additional_hash = local_hash
            untar(path)
            return local_hash
        return ""

    def download_image(self):
        url = self.image_tarball_url
        if url:
            path = config.comms.get_cube_image(url, self.uid)
            local_hash = get_file_sha1(path)
            if not self.image_tarball_hash:
                self.image_tarball_hash = local_hash
            untar(path)
            return local_hash
        else:
            # Retrieve image from image registry
            logging.debug(f"Retrieving {self.uid} image")
            cmd = f"mlcube configure --mlcube={self.cube_path}"
            proc = spawn(cmd)
            proc_out = combine_proc_sp_text(proc)
            logging.debug(proc_out)
            proc.close()
            return ""

    def download(self):
        """Downloads the required elements for an mlcube to run locally."""

        local_hashes = {
            "mlcube_hash": self.download_mlcube(),
            "parameters_hash": self.download_parameters(),
            "additional_files_tarball_hash": self.download_additional(),
            "image_tarball_hash": self.download_image(),
        }
        self.store_local_hashes(local_hashes)

    def is_valid(self) -> bool:
        """Checks the validity of the cube and related files through hash checking.

        Returns:
            bool: Wether the cube and related files match the expeced hashes
        """
        try:
            local_hashes = self.get_local_hashes()
        except FileNotFoundError:
            logging.warning("Local MLCube files not found. Defaulting to invalid")
            return False

        valid_cube = self.is_cube_valid
        valid_hashes = True
        server_hashes = self.todict()
        for key in local_hashes:
            if local_hashes[key]:
                if local_hashes[key] != server_hashes[key]:
                    valid_hashes = False
                    msg = f"{key.replace('_', ' ')} doesn't match"
                    config.ui.print_error(msg)

        return valid_cube and valid_hashes

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
        proc = spawn(cmd, timeout=timeout)
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

    def todict(self) -> Dict:
        return {
            "name": self.name,
            "git_mlcube_url": self.git_mlcube_url,
            "mlcube_hash": self.mlcube_hash,
            "git_parameters_url": self.git_parameters_url,
            "parameters_hash": self.parameters_hash,
            "image_tarball_url": self.image_tarball_url,
            "image_tarball_hash": self.image_tarball_hash,
            "additional_files_tarball_url": self.additional_files_tarball_url,
            "additional_files_tarball_hash": self.additional_hash,
            "state": self.state,
            "is_valid": self.is_cube_valid,
            "id": self.uid,
            "owner": self.owner,
            "metadata": self.metadata,
            "user_metadata": self.user_metadata,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    def write(self):
        cube_loc = str(Path(self.cube_path).parent)
        meta_file = os.path.join(cube_loc, config.cube_metadata_filename)
        os.makedirs(cube_loc, exist_ok=True)
        with open(meta_file, "w") as f:
            yaml.dump(self.todict(), f)
        return meta_file

    def upload(self):
        cube_dict = self.todict()
        updated_cube_dict = config.comms.upload_mlcube(cube_dict)
        return updated_cube_dict

    def get_local_hashes(self):
        cubes_storage = storage_path(config.cubes_storage)
        local_hashes_file = os.path.join(
            cubes_storage, str(self.uid), config.cube_hashes_filename
        )
        with open(local_hashes_file, "r") as f:
            local_hashes = yaml.safe_load(f)
        return local_hashes

    def store_local_hashes(self, local_hashes):
        cubes_storage = storage_path(config.cubes_storage)
        local_hashes_file = os.path.join(
            cubes_storage, str(self.uid), config.cube_hashes_filename
        )
        with open(local_hashes_file, "w") as f:
            yaml.dump(local_hashes, f)

    @classmethod
    def __get_local_dict(cls, uid):
        cubes_storage = storage_path(config.cubes_storage)
        meta_file = os.path.join(cubes_storage, uid, config.cube_metadata_filename)
        if not os.path.exists(meta_file):
            raise InvalidArgumentError(
                "The requested mlcube information could not be found locally"
            )
        with open(meta_file, "r") as f:
            meta = yaml.safe_load(f)
        return meta
