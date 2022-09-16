import os
import yaml
import pexpect
import logging
from typing import List
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
from medperf.ui.interface import UI
import medperf.config as config


class Cube(object):
    """
    Class representing an MLCube Container

    Medperf platform uses the MLCube container for components such as
    Dataset Preparation, Evaluation, and the Registered Models. MLCube
    containers are software containers (e.g., Docker and Singularity)
    with standard metadata and a consistent file-system level interface.
    """

    def __init__(
        self,
        uid: str,
        meta: dict,
        cube_path: str,
        params_path: str = None,
        additional_hash: str = None,
        image_tarball_hash: str = None,
    ):
        """Creates a Cube instance

        Args:
            uid (str): UID of the cube.
            meta (dict): Dict for additional information regarding the cube.
            cube_path (str): path to the mlcube.yaml file associated with this cube.
            params_path (str, optional): Location of the parameters.yaml file. if exists. Defaults to None.
            additional_hash (str, optional): Hash of the tarball file, if exists. Defaults to None.
            image_tarball_hash (str, optional): Hash of the image file, if exists. Defaults to None.
        """
        self.uid = uid
        self.meta = meta
        self.name = meta["name"]
        self.cube_path = cube_path
        self.params_path = params_path
        self.additional_hash = additional_hash
        self.image_tarball_hash = image_tarball_hash

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
            pretty_error(msg, config.ui)

        cubes = []
        for uid in uids:
            cube_path = os.path.join(cubes_storage, uid, config.cube_filename)
            meta_file = os.path.join(cubes_storage, uid, config.cube_metadata_filename)
            with open(meta_file, "r") as f:
                meta = yaml.safe_load(f)

            params_path = os.path.join(cubes_storage, uid, config.params_filename)
            if not os.path.exists(params_path):
                params_path = None

            local_hashes_file = os.path.join(
                cubes_storage, uid, config.cube_hashes_filename
            )
            with open(local_hashes_file, "r") as f:
                local_hashes = yaml.safe_load(f)
            additional_hash = local_hashes["additional_files_tarball_hash"]
            image_tarball_hash = local_hashes["image_tarball_hash"]

            cube = cls(
                uid, meta, cube_path, params_path, additional_hash, image_tarball_hash
            )
            cubes.append(cube)

        return cubes

    @classmethod
    def get(cls, cube_uid: str) -> "Cube":
        """Retrieves and creates a Cube instance from the comms. If cube already exists
        inside the user's computer then retrieves it from there.

        Args:
            cube_uid (str): UID of the cube.
            comms (Comms): Instance of the server interface.
            ui (UI): Instance of an UI implementation.

        Returns:
            Cube : a Cube instance with the retrieved data.
        """
        "Retrieve from local storage if cube already there"
        logging.debug(f"Retrieving the cube {cube_uid}")
        comms = config.comms
        ui = config.ui
        local_cube = list(
            filter(lambda cube: str(cube.uid) == str(cube_uid), cls.all(ui))
        )
        if len(local_cube) == 1:
            logging.debug("Found cube locally")
            return local_cube[0]

        meta = config.comms.get_cube_metadata(cube_uid)
        # Backwards compatibility for cubes with
        # tarball_url instead of additional_files_tarball_url
        old_files = "tarball_url"
        old_hash = "tarball_hash"
        add_files = "additional_files_tarball_url"
        add_hash = "additional_files_tarball_hash"
        if old_files in meta:
            meta[add_files] = meta[old_files]
            meta[add_hash] = meta[old_hash]
        cube_path = comms.get_cube(meta["git_mlcube_url"], cube_uid)
        params_path = None
        additional_path = None
        additional_hash = None
        image_path = None
        image_tarball_hash = None
        if "git_parameters_url" in meta and meta["git_parameters_url"]:
            url = meta["git_parameters_url"]
            params_path = comms.get_cube_params(url, cube_uid)
        if add_files in meta and meta[add_files]:
            url = meta[add_files]
            additional_path = comms.get_cube_additional(url, cube_uid)
            additional_hash = get_file_sha1(additional_path)
            untar(additional_path)
        if "image_tarball_url" in meta and meta["image_tarball_url"]:
            url = meta["image_tarball_url"]
            image_path = comms.get_cube_image(url, cube_uid)
            image_tarball_hash = get_file_sha1(image_path)
            untar(image_path)
        else:
            # Retrieve image from image registry
            logging.debug(f"Retrieving {cube_uid} image")
            cmd = f"mlcube configure --mlcube={cube_path}"
            proc = pexpect.spawn(cmd)
            proc_out = combine_proc_sp_text(proc, ui)
            logging.debug(proc_out)
            proc.close()

        local_hashes = {
            "additional_files_tarball_hash": additional_hash if additional_hash else "",
            "image_tarball_hash": image_tarball_hash if image_tarball_hash else "",
        }
        save_cube_metadata(meta, local_hashes)
        return cls(
            cube_uid, meta, cube_path, params_path, additional_hash, image_tarball_hash
        )

    def is_valid(self) -> bool:
        """Checks the validity of the cube and related files through hash checking.

        Returns:
            bool: Wether the cube and related files match the expeced hashes
        """
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

    def run(self, ui: UI, task: str, timeout: int = None, **kwargs):
        """Executes a given task on the cube instance

        Args:
            ui (UI): an instance of an UI implementation
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
        proc_out = combine_proc_sp_text(proc, ui)
        proc.close()
        logging.debug(proc_out)
        if proc.exitstatus != 0:
            ui.text = "\n"
            ui.print(proc_out)
            pretty_error("There was an error while executing the cube", ui)

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