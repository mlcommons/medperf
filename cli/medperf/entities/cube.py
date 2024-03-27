import os
import yaml
import logging
from typing import List, Dict, Optional, Union
from pydantic import Field
from pathlib import Path

from medperf.utils import (
    combine_proc_sp_text,
    log_storage,
    remove_path,
    generate_tmp_path,
    spawn_and_kill,
)
from medperf.entities.interface import Entity, Uploadable
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
from medperf.account_management import get_medperf_user_data


class Cube(Entity, Uploadable, MedperfSchema, DeployableSchema):
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

    def __init__(self, *args, **kwargs):
        """Creates a Cube instance

        Args:
            cube_desc (Union[dict, CubeModel]): MLCube Instance description
        """
        super().__init__(*args, **kwargs)

        self.generated_uid = self.name
        path = config.cubes_folder
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
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_cubes

        return comms_fn

    @classmethod
    def __local_all(cls) -> List["Cube"]:
        cubes = []
        cubes_folder = config.cubes_folder
        try:
            uids = next(os.walk(cubes_folder))[1]
            logging.debug(f"Local cubes found: {uids}")
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
        cube.download_config_files()
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

    def download_image(self):
        url = self.image_tarball_url
        tarball_hash = self.image_tarball_hash

        if url:
            _, local_hash = resources.get_cube_image(url, self.path, tarball_hash)
            self.image_tarball_hash = local_hash
        else:
            if config.platform == "docker":
                # For docker, image should be pulled before calculating its hash
                self._get_image_from_registry()
                self._set_image_hash_from_registry()
            elif config.platform == "singularity":
                # For singularity, we need the hash first before trying to convert
                self._set_image_hash_from_registry()

                image_folder = os.path.join(config.cubes_folder, config.image_path)
                if os.path.exists(image_folder):
                    for file in os.listdir(image_folder):
                        if file == self._converted_singularity_image_name:
                            return
                        remove_path(os.path.join(image_folder, file))

                self._get_image_from_registry()
            else:
                # TODO: such a check should happen on commands entrypoints, not here
                raise InvalidArgumentError("Unsupported platform")

    @property
    def _converted_singularity_image_name(self):
        return f"{self.image_hash}.sif"

    def _set_image_hash_from_registry(self):
        # Retrieve image hash from MLCube
        logging.debug(f"Retrieving {self.id} image hash")
        tmp_out_yaml = generate_tmp_path()
        cmd = f"mlcube --log-level {config.loglevel} inspect --mlcube={self.cube_path} --format=yaml"
        cmd += f" --platform={config.platform} --output-file {tmp_out_yaml}"
        logging.info(f"Running MLCube command: {cmd}")
        with spawn_and_kill(cmd, timeout=config.mlcube_inspect_timeout) as proc_wrapper:
            proc = proc_wrapper.proc
            combine_proc_sp_text(proc)
        if proc.exitstatus != 0:
            raise ExecutionError("There was an error while inspecting the image hash")
        with open(tmp_out_yaml) as f:
            mlcube_details = yaml.safe_load(f)
        remove_path(tmp_out_yaml)
        local_hash = mlcube_details["hash"]
        if self.image_hash and local_hash != self.image_hash:
            raise InvalidEntityError(
                f"Hash mismatch. Expected {self.image_hash}, found {local_hash}."
            )
        self.image_hash = local_hash

    def _get_image_from_registry(self):
        # Retrieve image from image registry
        logging.debug(f"Retrieving {self.id} image")
        cmd = f"mlcube --log-level {config.loglevel} configure --mlcube={self.cube_path} --platform={config.platform}"
        if config.platform == "singularity":
            cmd += f" -Psingularity.image={self._converted_singularity_image_name}"
        logging.info(f"Running MLCube command: {cmd}")
        with spawn_and_kill(
            cmd, timeout=config.mlcube_configure_timeout
        ) as proc_wrapper:
            proc = proc_wrapper.proc
            combine_proc_sp_text(proc)
        if proc.exitstatus != 0:
            raise ExecutionError("There was an error while retrieving the MLCube image")

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
            self.download_image()
        except InvalidEntityError as e:
            raise InvalidEntityError(f"MLCube {self.name} image file: {e}")

    def run(
        self,
        task: str,
        output_logs_file: str = None,
        string_params: Dict[str, str] = {},
        timeout: int = None,
        read_protected_input: bool = True,
        port=None,
        env_dict: dict = {},
        **kwargs,
    ):
        """Executes a given task on the cube instance

        Args:
            task (str): task to run
            string_params (Dict[str], optional): Extra parameters that can't be passed as normal function args.
                                                 Defaults to {}.
            timeout (int, optional): timeout for the task in seconds. Defaults to None.
            read_protected_input (bool, optional): Wether to disable write permissions on input volumes. Defaults to True.
            kwargs (dict): additional arguments that are passed directly to the mlcube command
        """
        # TODO: refactor this function. Move things to MLCube if possible
        kwargs.update(string_params)
        cmd = f"mlcube --log-level {config.loglevel} run"
        cmd += f" --mlcube={self.cube_path} --task={task} --platform={config.platform}"
        if task not in ["train", "start_aggregator"]:
            cmd += " --network=none"
        if config.gpus is not None:
            cmd += f" --gpus={config.gpus}"
        if read_protected_input:
            cmd += " --mount=ro"
        for k, v in kwargs.items():
            cmd_arg = f'{k}="{v}"'
            cmd = " ".join([cmd, cmd_arg])

        container_loglevel = config.container_loglevel
        if container_loglevel:
            env_dict["MEDPERF_LOGLEVEL"] = container_loglevel.upper()

        env_args_string = ""
        for key, val in env_dict.items():
            env_args_string += f"--env {key}={val} "
        env_args_string = env_args_string.strip()

        # TODO: we should override run args instead of what we are doing below
        #       we shouldn't allow arbitrary run args unless our client allows it
        if config.platform == "docker":
            # use current user
            cpu_args = self.get_config("docker.cpu_args") or ""
            gpu_args = self.get_config("docker.gpu_args") or ""
            cpu_args = " ".join([cpu_args, "-u $(id -u):$(id -g)"]).strip()
            gpu_args = " ".join([gpu_args, "-u $(id -u):$(id -g)"]).strip()
            if port is not None:
                cpu_args += f" -p {port}:{port}"
                gpu_args += f" -p {port}:{port}"
            cmd += f' -Pdocker.cpu_args="{cpu_args}"'
            cmd += f' -Pdocker.gpu_args="{gpu_args}"'
            if env_args_string:  # TODO: why MLCube UI is so brittle?
                env_args = self.get_config("docker.env_args") or ""
                env_args = " ".join([env_args, env_args_string]).strip()
                cmd += f' -Pdocker.env_args="{env_args}"'

        elif config.platform == "singularity":
            # use -e to discard host env vars, -C to isolate the container (see singularity run --help)
            run_args = self.get_config("singularity.run_args") or ""
            run_args = " ".join([run_args, "-eC"]).strip()
            run_args += " " + env_args_string
            cmd += f' -Psingularity.run_args="{run_args}"'
            # TODO: check if ports are already exposed. Think if this is OK
            # TODO: check if --env works

            # set image name in case of running docker image with singularity
            # Assuming we only accept mlcube.yamls with either singularity or docker sections
            # TODO: make checks on submitted mlcubes
            singularity_config = self.get_config("singularity")
            if singularity_config is None:
                cmd += (
                    f' -Psingularity.image="{self._converted_singularity_image_name}"'
                )
        else:
            raise InvalidArgumentError("Unsupported platform")

        # set accelerator count to zero to avoid unexpected behaviours and
        # force mlcube to only use --gpus to figure out GPU config
        cmd += " -Pplatform.accelerator_count=0"

        logging.info(f"Running MLCube command: {cmd}")
        with spawn_and_kill(cmd, timeout=timeout) as proc_wrapper:
            proc = proc_wrapper.proc
            proc_out = combine_proc_sp_text(proc)

        if output_logs_file is not None:
            with open(output_logs_file, "w") as f:
                f.write(proc_out)
        if proc.exitstatus != 0:
            raise ExecutionError("There was an error while executing the cube")

        log_storage()
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
        cubes_folder = config.cubes_folder
        meta_file = os.path.join(cubes_folder, str(uid), config.cube_metadata_filename)
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
