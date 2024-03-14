from __future__ import annotations

import re
import os
import grp
import csv
import signal
import yaml
import psutil
import socket
import random
import hashlib
import logging
import tarfile
import requests
import platform
import getpass
import docker
import pkg_resources
from glob import glob
import json
from pathlib import Path
import shutil
import subprocess
from pexpect import spawn
from datetime import datetime
from pydantic.datetime_parse import parse_datetime
from typing import List
from colorama import Fore, Style
from pexpect.exceptions import TIMEOUT
from git import Repo, GitCommandError
import medperf.config as config
from medperf.exceptions import ExecutionError, MedperfException


def get_file_hash(path: str) -> str:
    """Calculates the sha256 hash for a given file.

    Args:
        path (str): Location of the file of interest.

    Returns:
        str: Calculated hash
    """
    logging.debug("Calculating hash for file {}".format(path))
    BUF_SIZE = 65536
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha.update(data)

    sha_val = sha.hexdigest()
    logging.debug(f"Hash for file {path}: {sha_val}")
    return sha_val


def remove_path(path):
    """Cleans up a clutter object. In case of failure, it is moved to `.trash`"""

    # NOTE: We assume medperf will always have permissions to unlink
    # and rename clutter paths, since for now they are expected to live
    # in folders owned by medperf

    if not os.path.exists(path):
        return
    logging.info(f"Removing clutter path: {path}")

    # Don't delete symlinks
    if os.path.islink(path):
        os.unlink(path)
        return

    try:
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)
    except OSError as e:
        logging.error(f"Could not remove {path}: {str(e)}")
        move_to_trash(path)


def move_to_trash(path):
    trash_folder = config.trash_folder
    unique_path = os.path.join(trash_folder, generate_tmp_uid())
    os.makedirs(unique_path)
    shutil.move(path, unique_path)


def cleanup():
    """Removes clutter and unused files from the medperf folder structure."""
    if not config.cleanup:
        logging.info("Cleanup disabled")
        return

    for path in config.tmp_paths:
        remove_path(path)

    trash_folder = config.trash_folder
    if os.path.exists(trash_folder) and os.listdir(trash_folder):
        msg = "WARNING: Failed to premanently cleanup some files. Consider deleting"
        msg += f" '{trash_folder}' manually to avoid unnecessary storage."
        config.ui.print_warning(msg)


def get_uids(path: str) -> List[str]:
    """Retrieves the UID of all the elements in the specified path.

    Returns:
        List[str]: UIDs of objects in path.
    """
    logging.debug("Retrieving datasets")
    uids = next(os.walk(path))[1]
    logging.debug(f"Found {len(uids)} datasets")
    logging.debug(f"Datasets: {uids}")
    return uids


def pretty_error(msg: str):
    """Prints an error message with typer protocol

    Args:
        msg (str): Error message to show to the user
    """
    ui = config.ui
    logging.warning(
        "MedPerf had to stop execution. See logs above for more information"
    )
    if msg[-1] != ".":
        msg = msg + "."
    ui.print_error(msg)


def generate_tmp_uid() -> str:
    """Generates a temporary uid by means of getting the current timestamp
    with a random salt

    Returns:
        str: generated temporary uid
    """
    dt = datetime.utcnow()
    ts_int = int(datetime.timestamp(dt))
    salt = random.randint(-ts_int, ts_int)
    ts = str(ts_int + salt)
    return ts


def generate_tmp_path() -> str:
    """Generates a temporary path by means of getting the current timestamp
    with a random salt

    Returns:
        str: generated temporary path
    """
    tmp_path = os.path.join(config.tmp_folder, generate_tmp_uid())
    config.tmp_paths.append(tmp_path)
    return tmp_path


def untar(filepath: str, remove: bool = True) -> str:
    """Untars and optionally removes the tar.gz file

    Args:
        filepath (str): Path where the tar.gz file can be found.
        remove (bool): Wether to delete the tar.gz file. Defaults to True.

    Returns:
        str: location where the untared files can be found.
    """
    logging.info(f"Uncompressing tar.gz at {filepath}")
    addpath = str(Path(filepath).parent)
    tar = tarfile.open(filepath)
    tar.extractall(addpath)
    tar.close()

    # OS Specific issue: Mac Creates superfluous files with tarfile library
    [
        remove_path(spurious_file)
        for spurious_file in glob(addpath + "/**/._*", recursive=True)
    ]
    if remove:
        logging.info(f"Deleting {filepath}")
        remove_path(filepath)
    return addpath


def approval_prompt(msg: str) -> bool:
    """Helper function for prompting the user for things they have to explicitly approve.

    Args:
        msg (str): What message to ask the user for approval.

    Returns:
        bool: Wether the user explicitly approved or not.
    """
    logging.info("Prompting for user's approval")
    ui = config.ui
    approval = None
    while approval is None or approval not in "yn":
        approval = ui.prompt(msg.strip() + " ").lower()
    logging.info(f"User answered approval with {approval}")
    return approval == "y"


def dict_pretty_print(in_dict: dict, skip_none_values: bool = True):
    """Helper function for distinctively printing dictionaries with yaml format.

    Args:
        in_dict (dict): dictionary to print
        skip_none_values (bool): if fields with `None` values should be omitted
    """
    logging.debug(f"Printing dictionary to the user: {in_dict}")
    ui = config.ui
    ui.print()
    ui.print("=" * 20)
    if skip_none_values:
        in_dict = {k: v for (k, v) in in_dict.items() if v is not None}
    ui.print(yaml.dump(in_dict))
    logging.debug(f"Dictionary printed to the user: {in_dict}")
    ui.print("=" * 20)


class _MLCubeOutputFilter:
    def __init__(self, proc_pid: int):
        self.log_pattern = re.compile(
            r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \S+ \S+\[(\d+)\] (\S+) (.*)$"
        )
        # Clear log lines from color / style symbols before matching with regexp
        self.ansi_escape_pattern = re.compile(r"\x1b\[[0-9;]*[mGK]")
        self.proc_pid = str(proc_pid)

    def check_line(self, line: str) -> bool:
        """
        Args:
            line: line from mlcube output
        Returns:
            true if line should be filtered out (==saved to debug file only),
            false if line should be printed to user also
        """
        match = self.log_pattern.match(self.ansi_escape_pattern.sub("", line))
        if match:
            line_pid, matched_log_level_str, content = match.groups()
            matched_log_level = logging.getLevelName(matched_log_level_str)

            # if line matches conditions, it is just logged to debug; else, shown to user
            return (
                line_pid == self.proc_pid  # hide only `mlcube` framework logs
                and isinstance(matched_log_level, int)
                and matched_log_level < logging.INFO
            )  # hide only debug logs
        return False


def combine_proc_sp_text(proc: spawn) -> str:
    """Combines the output of a process and the spinner.
    Joins any string captured from the process with the
    spinner current text. Any strings ending with any other
    character from the subprocess will be returned later.

    Args:
        proc (spawn): a pexpect spawned child

    Returns:
        str: all non-carriage-return-ending string captured from proc
    """

    ui = config.ui
    proc_out = ""
    break_ = False
    log_filter = _MLCubeOutputFilter(proc.pid)

    while not break_:
        if not proc.isalive():
            break_ = True
        try:
            line = proc.readline()
        except TIMEOUT:
            logging.error("Process timed out")
            logging.debug(proc_out)
            raise ExecutionError("Process timed out")
        line = line.decode("utf-8", "ignore")

        if not line:
            continue

        # Always log each line just in case the final proc_out
        # wasn't logged for some reason
        logging.debug(line)
        proc_out += line
        if not log_filter.check_line(line):
            ui.print(f"{Fore.WHITE}{Style.DIM}{line.strip()}{Style.RESET_ALL}")

    logging.debug("MLCube process finished")
    logging.debug(proc_out)
    return proc_out


def get_folders_hash(paths: List[str]) -> str:
    """Generates a hash for all the contents of the fiven folders. This procedure
    hashes all the files in all passed folders, sorts them and then hashes that list.

    Args:
        paths List(str): Folders to hash.

    Returns:
        str: sha256 hash that represents all the folders altogether
    """
    hashes = []

    # The hash doesn't depend on the order of paths or folders, as the hashes get sorted after the fact
    for path in paths:
        for root, _, files in os.walk(path, topdown=False):
            for file in files:
                logging.debug(f"Hashing file {file}")
                filepath = os.path.join(root, file)
                hashes.append(get_file_hash(filepath))

    hashes = sorted(hashes)
    sha = hashlib.sha256()
    for hash in hashes:
        sha.update(hash.encode("utf-8"))
    hash_val = sha.hexdigest()
    logging.debug(f"Folder hash: {hash_val}")
    return hash_val


def list_files(startpath):
    tree_str = ""
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, "").count(os.sep)
        indent = " " * 4 * level

        tree_str += "{}{}/\n".format(indent, os.path.basename(root))
        subindent = " " * 4 * (level + 1)
        for f in files:
            tree_str += "{}{}\n".format(subindent, f)

    return tree_str


def log_storage():
    for folder in config.storage:
        folder = getattr(config, folder)
        logging.debug(list_files(folder))


def get_system_information():
    # Get basic system information
    system_info = {
        "Platform": platform.platform(),
        "Hostname": socket.gethostname(),
        "Processor": platform.processor(),
        "System Version": platform.version(),
        "Python Version": platform.python_version(),
    }
    return system_info


def get_memory_usage():
    # Get memory usage
    memory = psutil.virtual_memory()
    return {
        "Total Memory": memory.total,
        "Available Memory": memory.available,
        "Used Memory": memory.used,
        "Memory Usage Percentage": memory.percent,
    }


def get_disk_usage():
    # Get disk usage
    disk_usage = psutil.disk_usage("/")
    return {
        "Total Disk Space": disk_usage.total,
        "Used Disk Space": disk_usage.used,
        "Free Disk Space": disk_usage.free,
        "Disk Usage Percentage": disk_usage.percent,
    }


def get_user_information():
    # Get user information
    username = getpass.getuser()
    is_sudoers = "sudo" in [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
    is_docker_group = "docker" in [
        g.gr_name for g in grp.getgrall() if username in g.gr_mem
    ]
    return {
        "Username": username,
        "Is in Sudoers Group": is_sudoers,
        "Is in Docker Group": is_docker_group,
    }


def get_docker_information():
    try:
        exec_path = shutil.which("docker")
        client = docker.from_env()
        version = client.version()
        info = client.info()
        return {
            "Docker Installed": True,
            "Executable path": exec_path,
            "information": info,
            "Version": version,
        }
    except Exception as e:
        return {"Docker Installed": False, "Error": str(e)}


def get_singularity_information():
    try:
        exec_path = shutil.which("singularity")
        if exec_path is None:
            return {"Singularity installed": False}
        conf_path = "/usr/local/etc/singularity/singularity.conf"
        with open(conf_path, "r") as f:
            conf = f.readlines()
        conf_content = []
        for line in conf:
            if line.startswith("#") or len(line.strip()):
                continue
            conf_content.append(line.strip)
        config_dict = {}
        for line in conf_content:
            key, value = line.split("=")
            key = key.strip().lower()
            value = value.strip()
            if value.isdigit():
                value = int(value)
            config_dict[key] = value
        return {
            "Singularity installed": True,
            "Executable path": exec_path,
            "Configuration": config_dict,
        }
    except Exception as e:
        return {"Singularity installed": False, "Error": str(e)}


def get_configuration_variables():
    config_vars = vars(config)
    config_dict = {}
    for item in dir(config):
        if item.startswith("__"):
            continue
        config_dict[item] = config_vars[item]
    config_dict = filter_var_dict_for_yaml(config_dict)
    return config_dict


def filter_var_dict_for_yaml(unfiltered_dict):
    valid_types = (str, dict, list, int, float)
    filtered_dict = {}
    for key, value in unfiltered_dict.items():
        if not isinstance(value, valid_types) and value is not None:
            try:
                value = str(value)
            except Exception:
                value = "<OBJECT>"
        if isinstance(value, dict):
            value = filter_var_dict_for_yaml(value)
        filtered_dict[key] = value

    return filtered_dict


def get_storage_contents():
    storage_paths = config.storage.copy()
    storage_paths["credentials_folder"] = {
        "base": os.path.dirname(config.creds_folder),
        "name": os.path.basename(config.creds_folder),
    }
    ignore_paths = {"datasets_folder", "predictions_folder", "results_folder"}
    contents = {}

    for pathname, path in storage_paths.items():
        if pathname in ignore_paths:
            contents[pathname] = "<REDACTED>"
            continue
        full_path = os.path.join(path["base"], path["name"])
        p = subprocess.Popen(
            ["ls", "-lR", full_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output, _ = p.communicate()
        if p.returncode != 0:
            contents[pathname] = "Could not retrieve tree for storage paths"
        contents[pathname] = output

    return contents


def get_installed_packages():
    installed_packages = {}
    for package in pkg_resources.working_set:
        installed_packages[package.key] = package.version
    return installed_packages


def get_python_environment_information():
    environment_info = {
        "Operating System": platform.system(),
        "Operating System Release": platform.release(),
        "Operating System Version": platform.version(),
        "Python Implementation": platform.python_implementation(),
        "Python Version": platform.python_version(),
        "Python Compiler": platform.python_compiler(),
        "Python Build": platform.python_build(),
        "Machine Architecture": platform.machine(),
        "Processor Type": platform.processor(),
        "Python Executable": shutil.which("python"),
        "Installed Modules": get_installed_packages(),
    }
    return environment_info


def get_gpu_information():
    try:
        gpu_info = {}
        # Get GPU information
        p = subprocess.Popen(
            [
                "nvidia-smi",
                "--query-gpu=index,gpu_name,driver_version,compute_cap,memory.total",
                "--format=csv",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output, _ = p.communicate()
        if p.returncode != 0:
            raise ExecutionError("nvidia-smi not installed/available")
        gpus_data = [row for row in csv.DictReader(output.split("\n"))]
        gpu_info["GPU(s)"] = gpus_data

        # Get CUDA version
        p = subprocess.Popen(
            ["nvidia-smi", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        output, _ = p.communicate()
        if p.returncode != 0:
            raise ExecutionError("nvidia-smi not installed/available")
        output = output.split("\n")
        versions = [out.split(":") for out in output if len(out)]
        for key, value in versions:
            gpu_info[key.strip()] = value.strip()

        return gpu_info
    except (subprocess.CalledProcessError, ExecutionError, FileNotFoundError) as e:
        return {"Error": str(e)}


def log_machine_details():
    system_info = {}
    system_info["System Info"] = get_system_information()
    system_info["Memory Usage"] = get_memory_usage()
    system_info["Disk Usage"] = get_disk_usage()
    system_info["User Info"] = get_user_information()
    system_info["Docker Info"] = get_docker_information()
    system_info["Singularity Info"] = get_singularity_information()
    system_info["Medperf Configuration"] = get_configuration_variables()
    system_info["Medperf Storage Contents"] = get_storage_contents()
    system_info["Python Environment"] = get_python_environment_information()
    system_info["GPU(s) Information"] = get_gpu_information()

    debug_dict = {"Machine Details": system_info}

    logging.info(yaml.dump(debug_dict, default_flow_style=False))


def sanitize_json(data: dict) -> dict:
    """Makes sure the input data is JSON compliant.

    Args:
        data (dict): dictionary containing data to be represented as JSON.

    Returns:
        dict: sanitized dictionary
    """
    json_string = json.dumps(data)
    json_string = re.sub(r"\bNaN\b", '"nan"', json_string)
    json_string = re.sub(r"(-?)\bInfinity\b", r'"\1Infinity"', json_string)
    data = json.loads(json_string)
    return data


def log_response_error(res, warn=False):
    # NOTE: status 403 might be also returned if a requested resource doesn't exist
    if warn:
        logging_method = logging.warning
    else:
        logging_method = logging.error

    logging_method(f"Obtained response with status code: {res.status_code}")
    try:
        logging_method(res.json())
    except requests.exceptions.JSONDecodeError:
        logging_method("JSON Response could not be parsed. Showing response text:")
        logging_method(res.text)


def format_errors_dict(errors_dict: dict):
    """Reformats the error details from a field-error(s) dictionary into a human-readable string for printing"""
    error_msg = ""
    for field, errors in errors_dict.items():
        error_msg += "\n"
        if isinstance(field, tuple):
            field = field[0]
        error_msg += f"- {field}: "
        if isinstance(errors, str):
            error_msg += errors
        elif len(errors) == 1:
            # If a single error for a field is given, don't create a sublist
            error_msg += errors[0]
        else:
            # Create a sublist otherwise
            for e_msg in errors:
                error_msg += "\n"
                error_msg += f"\t- {e_msg}"
    return error_msg


def get_cube_image_name(cube_path: str) -> str:
    """Retrieves the singularity image name of the mlcube by reading its mlcube.yaml file"""
    cube_config_path = os.path.join(cube_path, config.cube_filename)
    with open(cube_config_path, "r") as f:
        cube_config = yaml.safe_load(f)

    try:
        # TODO: Why do we check singularity only there? Why not docker?
        return cube_config["singularity"]["image"]
    except KeyError:
        msg = "The provided mlcube doesn't seem to be configured for singularity"
        raise MedperfException(msg)


def filter_latest_associations(associations, entity_key):
    """Given a list of entity-benchmark associations, this function
    retrieves a list containing the latest association of each
    entity instance.

    Args:
        associations (list[dict]): the list of associations
        entity_key (str): either "dataset" or "model_mlcube"

    Returns:
        list[dict]: the list containing the latest association of each
                    entity instance.
    """

    associations.sort(key=lambda assoc: parse_datetime(assoc["created_at"]))
    latest_associations = {}
    for assoc in associations:
        entity_id = assoc[entity_key]
        latest_associations[entity_id] = assoc

    latest_associations = list(latest_associations.values())
    return latest_associations


def check_for_updates() -> None:
    """Check if the current branch is up-to-date with its remote counterpart using GitPython."""
    repo = Repo(config.BASE_DIR)
    if repo.bare:
        logging.debug("Repo is bare")
        return

    logging.debug(f"Current git commit: {repo.head.commit.hexsha}")

    try:
        for remote in repo.remotes:
            remote.fetch()

        if repo.head.is_detached:
            logging.debug("Repo is in detached state")
            return

        current_branch = repo.active_branch
        tracking_branch = current_branch.tracking_branch()

        if tracking_branch is None:
            logging.debug("Current branch does not track a remote branch.")
            return
        if current_branch.commit.hexsha == tracking_branch.commit.hexsha:
            logging.debug("No git branch updates.")
            return

        logging.debug(
            f"Git branch updates found: {current_branch.commit.hexsha} -> {tracking_branch.commit.hexsha}"
        )
        config.ui.print_warning(
            "MedPerf client updates found. Please, update your MedPerf installation."
        )
    except GitCommandError as e:
        logging.debug(
            "Exception raised during updates check. Maybe user checked out repo with git@ and private key"
            " or repo is in detached / non-tracked state?"
        )
        logging.debug(e)


class spawn_and_kill:
    def __init__(self, cmd, timeout=None, *args, **kwargs):
        self.cmd = cmd
        self.timeout = timeout
        self._args = args
        self._kwargs = kwargs
        self.proc: spawn
        self.exception_occurred = False

    @staticmethod
    def spawn(*args, **kwargs):
        return spawn(*args, **kwargs)

    def killpg(self):
        os.killpg(self.pid, signal.SIGINT)

    def __enter__(self):
        self.proc = self.spawn(
            self.cmd, timeout=self.timeout, *self._args, **self._kwargs
        )
        self.pid = self.proc.pid
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.exception_occurred = True
            # Forcefully kill the process group if any exception occurred, in particular,
            # - KeyboardInterrupt (user pressed Ctrl+C in terminal)
            # - any other medperf exception like OOM or bug
            # - pexpect.TIMEOUT
            logging.info(f"Killing ancestor processes because of exception: {exc_val=}")
            self.killpg()

        self.proc.close()
        self.proc.wait()
        # Return False to propagate exceptions, if any
        return False
