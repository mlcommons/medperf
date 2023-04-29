from __future__ import annotations

import re
import os
import yaml
import random
import hashlib
import logging
from logging import handlers
import tarfile
import requests
from medperf.config_managment import ConfigManager
from glob import glob
import json
from pathlib import Path
from shutil import rmtree
from pexpect import spawn
from datetime import datetime
from typing import List
from colorama import Fore, Style
from pexpect.exceptions import TIMEOUT

import medperf.config as config
from medperf.logging.filters.redacting_filter import RedactingFilter
from medperf.exceptions import ExecutionError, InvalidEntityError, MedperfException


def setup_logging(log_lvl):
    log_fmt = "%(asctime)s | %(levelname)s: %(message)s"
    log_file = storage_path(config.log_file)
    handler = handlers.RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    handler.setFormatter(logging.Formatter(log_fmt))
    logging.basicConfig(
        level=log_lvl,
        handlers=[handler],
        format=log_fmt,
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    sensitive_pattern = re.compile(
        r"""(["']?(password|pwd|token)["']?[:=] ?)["'][^\n\[\]{}"']*["']"""
    )

    redacting_filter = RedactingFilter(patterns=[sensitive_pattern])
    requests_logger = logging.getLogger("requests")
    requests_logger.addHandler(handler)
    requests_logger.setLevel(log_lvl)
    logger = logging.getLogger()
    logger.addFilter(redacting_filter)


def delete_credentials():
    config_p = read_config()
    del config_p.active_profile[config.credentials_keyword]
    write_config(config_p)


def set_credentials(token):
    config_p = read_config()
    config_p.active_profile[config.credentials_keyword] = token
    write_config(config_p)


def read_credentials():
    config_p = read_config()
    token = config_p.active_profile.get(config.credentials_keyword, None)
    return token


def set_current_user(current_user: dict):
    config_p = read_config()
    config_p.active_profile["current_user"] = current_user
    write_config(config_p)


def get_current_user():
    config_p = read_config()
    try:
        current_user = config_p.active_profile["current_user"]
    except KeyError:
        raise MedperfException(
            "Couldn't retrieve current user information. Please login again"
        )
    return current_user


def default_profile():
    # NOTE: this function is only usable before config is actually initialized.
    # using this function when another profile is activated will not load the defaults
    return {param: getattr(config, param) for param in config.configurable_parameters}


def read_config():
    config_p = ConfigManager()
    config_path = base_storage_path(config.config_path)
    config_p.read(config_path)
    return config_p


def write_config(config_p: ConfigManager):
    config_path = base_storage_path(config.config_path)
    config_p.write(config_path)


def set_custom_config(args: dict):
    """Function to set parameters defined by the user

    Args:
        args (dict): custom config params
    """
    for param in args:
        val = args[param]
        setattr(config, param, val)


def storage_path(subpath: str):
    """Helper function that converts a path to deployment storage-related path"""
    server_path = config.server.split("//")[1]
    server_path = re.sub(r"[.:]", "_", server_path)
    return os.path.join(config.storage, server_path, subpath)


def base_storage_path(subpath: str):
    """Helper function that converts a path to base storage-related path"""
    return os.path.join(config.storage, subpath)


def get_file_sha1(path: str) -> str:
    """Calculates the sha1 hash for a given file.

    Args:
        path (str): Location of the file of interest.

    Returns:
        str: Calculated hash
    """
    logging.debug("Calculating SHA1 hash for file {}".format(path))
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)

    sha_val = sha1.hexdigest()
    logging.debug(f"SHA1 hash for file {path}: {sha_val}")
    return sha_val


def init_storage():
    """Builds the general medperf folder structure."""
    logging.info("Initializing storage")
    parent = config.storage
    data = storage_path(config.data_storage)
    cubes = storage_path(config.cubes_storage)
    results = storage_path(config.results_storage)
    tmp = storage_path(config.tmp_storage)
    bmks = storage_path(config.benchmarks_storage)
    demo = storage_path(config.demo_data_storage)
    log = storage_path(config.logs_storage)
    imgs = base_storage_path(config.images_storage)
    tests = storage_path(config.test_storage)

    dirs = [parent, bmks, data, cubes, results, tmp, demo, log, imgs, tests]
    for dir in dirs:
        logging.info(f"Creating {dir} directory")
        try:
            os.makedirs(dir, exist_ok=True)
        except FileExistsError:
            logging.warning(f"Tried to create existing folder {dir}")


def init_config():
    """builds the initial configuration file"""
    os.makedirs(config.storage, exist_ok=True)
    config_file = base_storage_path(config.config_path)
    if os.path.exists(config_file):
        return

    config_p = ConfigManager()
    config_p[config.default_profile_name] = default_profile()
    config_p[config.test_profile_name] = default_profile()
    config_p[config.test_profile_name]["server"] = config.local_server
    config_p[config.test_profile_name]["certificate"] = config.local_certificate

    config_p.activate(config.default_profile_name)
    config_p.write(config_file)


def set_unique_tmp_config():
    """Set current process' temporary unique storage
    Enables simultaneous execution without cleanup collision
    """
    pid = str(os.getpid())
    config.tmp_storage += pid


def cleanup_tmp_storage():
    """Cleans up the temporary storage folder."""
    tmp_storage = storage_path(config.tmp_storage)
    for path in os.listdir(tmp_storage):
        path = os.path.join(tmp_storage, path)
        try:
            cleanup_path(path)
        except OSError as e:
            logging.error(
                f"Cleanup failed: Could not remove {path} from tmp storage: {str(e)}"
            )
    if os.listdir(tmp_storage):
        msg = f'Failed to completely remove "{tmp_storage}".'
        msg += " Consider removing this folder manually to avoid unnecessary storage."
        config.ui.print_warning(msg)
    else:
        os.remove(tmp_storage)


def handle_cleanup_failure(path):
    """Moves a folder/file to tmp storage. This function is used
    when the MedPerf fails to remove a certain path."""
    try:
        os.rename(path, generate_tmp_path())
    except OSError as e:
        logging.error(
            f"Cleanup handler failed: Could not move {path} to tmp storage: {str(e)}"
        )
        msg = f'Failed to cleanup path: "{path}".'
        msg += " Remove these files manually BEFORE running another command"
        config.ui.print_warning(msg)


def cleanup_path(path):
    """Removes a path whether it is a file or a folder. If the
    path is a symlink, it only gets unlinked."""
    if os.path.exists(path):
        logging.info(f"Removing clutter path: {path}")
        if os.path.islink(path):
            os.unlink(path)
        elif os.path.isfile(path):
            os.remove(path)
        else:
            rmtree(path)


def cleanup():
    """Removes clutter and unused files from the medperf folder structure."""
    if not config.cleanup:
        logging.info("Cleanup disabled")
        return
    for path in config.cleanup_paths:
        try:
            cleanup_path(path)
        except OSError as e:
            logging.error(f"Cleanup failed: Could not remove {path}: {str(e)}")
            handle_cleanup_failure(path)
    cleanup_tmp_storage()


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
    tmp_path = os.path.join(config.tmp_storage, generate_tmp_uid())
    tmp_path = storage_path(tmp_path)
    return os.path.abspath(tmp_path)


def check_cube_validity(cube: "Cube"):
    """Helper function for pretty printing the cube validity process.

    Args:
        cube (Cube): Cube to check for validity
    """
    logging.info(f"Checking cube {cube.name} validity")
    ui = config.ui
    ui.text = "Checking cube MD5 hash..."
    if not cube.valid():
        raise InvalidEntityError("MD5 hash doesn't match")
    logging.info(f"Cube {cube.name} is valid")
    ui.print(f"> {cube.name} MD5 hash check complete")


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
        os.remove(spurious_file)
        for spurious_file in glob(addpath + "/**/._*", recursive=True)
    ]
    if remove:
        logging.info(f"Deleting {filepath}")
        os.remove(filepath)
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


def combine_proc_sp_text(proc: spawn) -> str:
    """Combines the output of a process and the spinner.
    Joins any string captured from the process with the
    spinner current text. Any strings ending with any other
    character from the subprocess will be returned later.

    Args:
        proc (spawn): a pexpect spawned child
        ui (UI): An instance of an UI implementation

    Returns:
        str: all non-carriage-return-ending string captured from proc
    """
    ui = config.ui
    static_text = ui.text
    proc_out = ""
    while proc.isalive():
        try:
            line = byte = proc.read(1)
        except TIMEOUT:
            logging.error("Process timed out")
            raise ExecutionError("Process timed out")

        while byte and not re.match(b"[\r\n]", byte):
            byte = proc.read(1)
            line += byte
        if not byte:
            break
        line = line.decode("utf-8", "ignore")
        if line:
            # add to proc_out list for logging
            proc_out += line
        ui.text = (
            f"{static_text} {Fore.WHITE}{Style.DIM}{line.strip()}{Style.RESET_ALL}"
        )

    return proc_out


def get_folder_sha1(path: str) -> str:
    """Generates a hash for all the contents of the folder. This procedure
    hashes all of the files in the folder, sorts them and then hashes that list.

    Args:
        path (str): Folder to hash

    Returns:
        str: sha1 hash of the whole folder
    """
    hashes = []
    for root, _, files in os.walk(path, topdown=False):
        for file in files:
            logging.debug(f"Hashing file {file}")
            filepath = os.path.join(root, file)
            hashes.append(get_file_sha1(filepath))

    hashes = sorted(hashes)
    sha1 = hashlib.sha1()
    for hash in hashes:
        sha1.update(hash.encode("utf-8"))
    hash_val = sha1.hexdigest()
    logging.debug(f"Folder hash: {hash_val}")
    return hash_val


def list_files(startpath):
    tree_str = ""
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, "").count(os.sep)
        indent = " " * 4 * (level)

        tree_str += "{}{}/\n".format(indent, os.path.basename(root))
        subindent = " " * 4 * (level + 1)
        for f in files:
            tree_str += "{}{}\n".format(subindent, f)

    return tree_str


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
        logging_method("JSON Response could not be parsed. Showing response content:")
        logging_method(res.content)


def get_cube_image_name(cube_path: str) -> str:
    """Retrieves the singularity image name of the mlcube by reading its mlcube.yaml file"""
    cube_config_path = os.path.join(cube_path, config.cube_filename)
    with open(cube_config_path, "r") as f:
        cube_config = yaml.safe_load(f)

    try:
        return cube_config["singularity"]["image"]
    except KeyError:
        msg = "The provided mlcube doesn't seem to be configured for singularity"
        raise MedperfException(msg)
