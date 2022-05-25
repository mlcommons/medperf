import os
import yaml
import pexpect
import logging
from typing import List
from pathlib import Path

from medperf.utils import (
    approval_prompt,
    get_file_sha1,
    pretty_error,
    untar,
    combine_proc_sp_text,
    list_files,
    storage_path,
)
from medperf.ui.interface import UI
import medperf.config as config
from medperf.comms.interface import Comms


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
    def all(cls, ui: UI) -> List["Cube"]:
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
            pretty_error(msg, ui)

        cubes = []
        for uid in uids:
            cube_path = os.path.join(cubes_storage, uid, config.cube_filename)
            with open(cube_path, "r") as f:
                meta = yaml.safe_load(f)

            params_path = os.path.join(cubes_storage, uid, config.params_filename)
            if not os.path.exists(params_path):
                params_path = None
            cube = cls(uid, meta, cube_path, params_path)
            cubes.append(cube)

        return cubes

    @classmethod
    def get(cls, cube_uid: str, comms: Comms, ui: UI) -> "Cube":
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
        local_cube = list(
            filter(lambda cube: str(cube.uid) == str(cube_uid), cls.all(ui))
        )
        if len(local_cube) == 1:
            return local_cube[0]

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
            untar(additional_path)

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

    def run(self, ui: UI, task: str, timeout: int = None, **kwargs):
        """Executes a given task on the cube instance

        Args:
            ui (UI): an instance of an UI implementation
            task (str): task to run
            timeout (int, optional): timeout for the task in seconds. Defaults to None.
            kwargs (dict): additional arguments that are passed directly to the mlcube command
        """
        cmd = f"mlcube run --mlcube={self.cube_path} --task={task}"
        for k, v in kwargs.items():
            cmd_arg = f"{k}={v}"
            cmd = " ".join([cmd, cmd_arg])
        logging.info(f"Running MLCube command: {cmd}")
        proc = pexpect.spawn(cmd, timeout=timeout)
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

    def request_association_approval(self, benchmark: "Benchmark", ui: UI) -> bool:
        """Prompts the user for approval concerning associating a cube with a benchmark.

        Args:
            benchmark (Benchmark): Benchmark to be associated with
            ui (UI): Instance of an UI interface

        Returns:
            bool: wether the user gave consent or not
        """

        msg = "Please confirm that you would like to associate "
        msg += f"the MLCube '{self.name}' with the benchmark '{benchmark.name}' [Y/n]"
        approved = approval_prompt(msg, ui)
        return approved
