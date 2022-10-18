import os
import yaml
import pexpect
import logging
from typing import List, Dict
from pathlib import Path

from medperf.utils import (
    save_cube_metadata,
    get_file_sha1,
    pretty_error,
    untar,
    combine_proc_sp_text,
    list_files,
    storage_path,
)
from medperf.entities.interface import Entity
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
            uid (str): UID of the cube.
            meta (dict): Dict for additional information regarding the cube.
            cube_path (str): path to the mlcube.yaml file associated with this cube.
            params_path (str, optional): Location of the parameters.yaml file. if exists. Defaults to None.
            additional_hash (str, optional): Hash of the tarball file, if exists. Defaults to None.
            image_tarball_hash (str, optional): Hash of the image file, if exists. Defaults to None.
        """
        self.uid = cube_dict["id"]
        self.name = cube_dict["name"]
        self.git_mlcube_url = cube_dict["git_mlcube_url"]
        self.git_parameters_url = cube_dict["git_parameters_url"]
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

        self.cube_path = None
        self.params_path = None
        self.local_additional_hash = None
        self.local_image_hash = None

        if self.uid:
            cubes_storage = storage_path(config.cubes_storage)
            self.cube_path = os.path.join(cubes_storage, self.uid, config.cube_filename)
            self.params_path = os.path.join(
                cubes_storage, self.uid, config.params_filename
            )

    @classmethod
    def all(cls) -> List["Cube"]:
        """Class method for retrieving all cubes stored on the user's machine.

        Args:
            ui (UI): Instance of an UI implementation.

        Returns:
            List[Cube]: List containing all cubes found locally
        """
        logging.info("Retrieving all local cubes")
        cubes_storage = storage_path(config.cubes_storage)
        try:
            uids = next(os.walk(cubes_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over cubes directory"
            logging.warning(msg)
            pretty_error(msg)

        cubes = []
        for uid in uids:
            meta_file = os.path.join(cubes_storage, uid, config.cube_metadata_filename)
            with open(meta_file, "r") as f:
                meta = yaml.safe_load(f)
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
        "Retrieve from local storage if cube already there"
        logging.debug(f"Retrieving the cube {cube_uid}")
        comms = config.comms
        local_cube = list(
            filter(lambda cube: str(cube.uid) == str(cube_uid), cls.all())
        )
        if len(local_cube) == 1:
            logging.debug("Found cube locally")
            return local_cube[0]

        meta = comms.get_cube_metadata(cube_uid)
        cube = cls(meta)
        cube.download()
        local_hashes = {
            "additional_files_tarball_hash": cube.additional_hash
            if cube.additional_hash
            else "",
            "image_tarball_hash": cube.image_tarball_hash
            if cube.image_tarball_hash
            else "",
        }
        save_cube_metadata(meta, local_hashes)
        return cube

    def download(self):
        """Downloads the required elements for an mlcube to run locally.
        """
        comms = config.comms
        ui = config.ui
        cube_uid = self.uid
        self.cube_path = comms.get_cube(self.git_mlcube_url, cube_uid)
        if self.git_parameters_url:
            url = self.git_parameters_url
            self.params_path = comms.get_cube_params(url, cube_uid)
        if self.additional_files_tarball_url:
            url = self.additional_files_tarball_url
            additional_path = comms.get_cube_additional(url, cube_uid)
            if not self.additional_hash:
                # log interactive ui only during submission
                ui.text = "Generating additional file hash"
            self.local_additional_hash = get_file_sha1(additional_path)
            if not self.additional_hash:
                ui.print("Additional file hash generated")
                self.additional_hash = self.local_additional_hash
            untar(additional_path)
        if self.image_tarball_url:
            url = self.image_tarball_url
            image_path = comms.get_cube_image(url, cube_uid)
            if not self.image_tarball_hash:
                # log interactive ui only during submission
                ui.text = "Generating image file hash"
            self.local_image_hash = get_file_sha1(image_path)
            if not self.image_tarball_hash:
                ui.print("Image file hash generated")
                self.image_tarball_hash = self.local_image_hash
            untar(image_path)
        else:
            # Retrieve image from image registry
            logging.debug(f"Retrieving {cube_uid} image")
            cmd = f"mlcube configure --mlcube={self.cube_path}"
            proc = pexpect.spawn(cmd)
            proc_out = combine_proc_sp_text(proc)
            logging.debug(proc_out)
            proc.close()

    def is_valid(self) -> bool:
        """Checks the validity of the cube and related files through hash checking.

        Returns:
            bool: Wether the cube and related files match the expeced hashes
        """
        # local_hashes_file = os.path.join(
        #     cubes_storage, uid, config.cube_hashes_filename
        # )
        # with open(local_hashes_file, "r") as f:
        #     local_hashes = yaml.safe_load(f)
        # additional_hash = local_hashes["additional_files_tarball_hash"]
        # image_tarball_hash = local_hashes["image_tarball_hash"]

        add_files = "additional_files_tarball_url"
        add_hash = "additional_files_tarball_hash"
        valid_cube = self.meta["is_valid"]
        has_additional = add_files in self.meta and self.meta[add_files]
        if has_additional:
            valid_additional = self.additional_hash == self.meta[add_hash]
        else:
            valid_additional = True

        has_image = "image_tarball_url" in self.meta and self.meta["image_tarball_url"]
        if has_image:
            valid_image = self.image_tarball_hash == self.meta["image_tarball_hash"]
        else:
            valid_image = True
        return valid_cube and valid_additional and valid_image

    def run(self, task: str, timeout: int = None, **kwargs):
        """Executes a given task on the cube instance

        Args:
            task (str): task to run
            timeout (int, optional): timeout for the task in seconds. Defaults to None.
            kwargs (dict): additional arguments that are passed directly to the mlcube command
        """
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
            raise RuntimeError("There was an error while executing the cube")

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
        return self.meta

    def upload(self) -> int:
        cube_uid = config.comms.upload_mlcube(self.todict())
        self.uid = cube_uid
        return self.uid
