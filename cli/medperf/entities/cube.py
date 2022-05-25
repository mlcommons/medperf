import logging
import yaml
import os
from pathlib import Path
import pexpect

from medperf.comms import Comms
from medperf.ui import UI
from medperf import config
from medperf.utils import (
    get_file_sha1,
    pretty_error,
    untar_additional,
    combine_proc_sp_text,
    list_files,
)


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
    ):
        """Creates a Cube instance

        Args:
            uid (str): UID of the cube.
            meta (dict): Dict for additional information regarding the cube.
            cube_path (str): path to the mlcube.yaml file associated with this cube.
            params_path (str, optional): Location of the parameters.yaml file. if exists. Defaults to None.
            additional_hash (str, optional): Hash of the tarball file, if exists. Defaults to None.
        """
        self.uid = uid
        self.meta = meta
        self.name = meta["name"]
        self.cube_path = cube_path
        self.params_path = params_path
        self.additional_hash = additional_hash

    @classmethod
    def get(cls, cube_uid: str, comms: Comms) -> "Cube":
        """Retrieves and creates a Cube instance from the comms

        Args:
            cube_uid (str): UID of the cube.
            comms (Comms): Instance of the server interface.

        Returns:
            Cube : a Cube instance with the retrieved data.
        """
        cube_uid = cube_uid
        meta = comms.get_cube_metadata(cube_uid)
        cube_path = comms.get_cube(meta["git_mlcube_url"], cube_uid)
        params_path = None
        additional_path = None
        additional_hash = None
        if "git_parameters_url" in meta and meta["git_parameters_url"]:
            url = meta["git_parameters_url"]
            params_path = comms.get_cube_params(url, cube_uid)
        if "tarball_url" in meta and meta["tarball_url"]:
            url = meta["tarball_url"]
            additional_path = comms.get_cube_additional(url, cube_uid)
            additional_hash = get_file_sha1(additional_path)
            untar_additional(additional_path)

        return cls(cube_uid, meta, cube_path, params_path, additional_hash)

    def is_valid(self) -> bool:
        """Checks the validity of the cube and related files through hash checking.

        Returns:
            bool: Wether the cube and related files match the expeced hashes
        """
        has_additional = "tarball_url" in self.meta and self.meta["tarball_url"]
        if has_additional:
            valid_additional = self.additional_hash == self.meta["tarball_hash"]
        else:
            valid_additional = True
        return valid_additional

    def run(self, ui: UI, task: str, **kwargs):
        """Executes a given task on the cube instance

        Args:
            ui (UI): an instance of an UI implementation
            task (str): task to run
            kwargs (dict): additional arguments that are passed directly to the mlcube command
        """
        cmd = f"mlcube run --mlcube={self.cube_path} --task={task}"
        for k, v in kwargs.items():
            cmd_arg = f"{k}={v}"
            cmd = " ".join([cmd, cmd_arg])
        logging.info(f"Running MLCube command: {cmd}")
        proc = pexpect.spawn(cmd, timeout=None)
        proc_out = combine_proc_sp_text(proc, ui)
        proc.close()
        logging.debug(proc_out)
        if proc.exitstatus != 0:
            ui.text = "\n"
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
                output for the desired task
        """
        with open(self.cube_path, "r") as f:
            cube = yaml.safe_load(f)

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
