from __future__ import annotations

import re
import os
import sys
import yaml
import typer
import random
import hashlib
import logging
import tarfile
import configparser
from glob import glob
import json
from pathlib import Path
from shutil import rmtree
from pexpect import spawn
from datetime import datetime
from typing import List, Tuple
from colorama import Fore, Style
from pexpect.exceptions import TIMEOUT

import medperf.config as config
from medperf.ui.interface import UI


def parse_context_args(ctx_args: List[str]) -> dict:
    """Parses extra arguments received from typer into a dictionary of args

    Args:
        ctx_args (List[str]): List of extra cli arguments

    Returns:
        dict: dictionary of key-value cli arguments
    """
    args = []
    for arg in ctx_args:
        args += arg.split("=")

    assert len(args) % 2 == 0, "A malformed set of arguments was passed"
    cli_args = {}
    for idx in range(0, len(args), 2):
        key = args[idx]
        val = args[idx + 1]
        
        assert key[:2] == "--", "Could not identify an argument name"
        cli_args[key[2:]] = val

    return cli_args


def set_custom_config(args: dict):
    """Function to set parameters defined by the user

    Args:
        args (dict): custom config params
    """
    params = config.customizable_params
    for param in params:
        val = getattr(config, param)
        if param in args:
            val = args[param]
        setattr(config, param, val)


def load_config(profile: str) -> dict:
    """Loads the configuration parameters associated to a profile

    Args:
        profile (str): profile name

    Returns:
        dict: configuration parameters
    """
    config_p = configparser.ConfigParser()
    config_file = os.path.join(config.storage, config.config_path)
    config_p.read(config_file)
    # Set current profile
    config.profile = profile
    return config_p[profile]


def storage_path(subpath: str):
    """Helper function that converts a path to storage-related path"""
    server_path = config.server.split('//')[1]
    server_path = server_path.replace('.', '_')
    return os.path.join(config.storage, server_path, subpath)


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
    """Builds the general medperf folder structure.
    """
    logging.info("Initializing storage")
    parent = config.storage
    data = storage_path(config.data_storage)
    cubes = storage_path(config.cubes_storage)
    results = storage_path(config.results_storage)
    tmp = storage_path(config.tmp_storage)
    bmks = storage_path(config.benchmarks_storage)
    demo = storage_path(config.demo_data_storage)
    log = storage_path(config.logs_storage)

    dirs = [parent, bmks, data, cubes, results, tmp, demo, log]
    for dir in dirs:
        logging.info(f"Creating {dir} directory")
        try:
            os.makedirs(dir, exist_ok=True)
        except FileExistsError:
            logging.warning(f"Tried to create existing folder {dir}")


def init_config():
    """builds the initial configuration file
    """
    config_file = os.path.join(config.storage, config.config_path)
    if os.path.exists(config_file):
        return
    config_p = configparser.ConfigParser()
    config_p["default"] = {}
    config_p["test"] = {}
    config_p["test"]["server"] = config.local_server
    config_p["test"]["certificate"] = config.local_certificate

    with open(config_file, "w") as f:
        config_p.write(f)


def cleanup():
    """Removes clutter and unused files from the medperf folder structure.
    """
    if not config.cleanup:
        logging.info("Cleanup disabled")
        return
    tmp_path = storage_path(config.tmp_storage)
    if os.path.exists(tmp_path):
        logging.info("Removing temporary data storage")
        try:
            rmtree(tmp_path)
        except OSError as e:
            logging.error(f"Could not remove temporary data storage: {e}")
            config.ui.print_error(
                "Could not remove temporary data storage. For more information check the logs."
            )

    cleanup_dsets()
    cleanup_cubes()
    cleanup_benchmarks()


def cleanup_dsets():
    """Removes clutter related to datsets
    """
    dsets_path = storage_path(config.data_storage)
    dsets = get_uids(dsets_path)
    tmp_prefix = config.tmp_prefix
    test_prefix = config.test_dset_prefix
    clutter_dsets = [
        dset
        for dset in dsets
        if dset.startswith(tmp_prefix) or dset.startswith(test_prefix)
    ]

    for dset in clutter_dsets:
        logging.info(f"Removing clutter dataset: {dset}")
        dset_path = os.path.join(dsets_path, dset)
        if os.path.exists(dset_path):
            try:
                rmtree(dset_path)
            except OSError as e:
                logging.error(f"Could not remove dataset {dset}: {e}")
                config.ui.print_error(
                    f"Could not remove dataset {dset}. For more information check the logs."
                )


def cleanup_cubes():
    """Removes clutter related to cubes
    """
    cubes_path = storage_path(config.cubes_storage)
    cubes = get_uids(cubes_path)
    test_prefix = config.test_cube_prefix
    submission = config.cube_submission_id
    clutter_cubes = [
        cube for cube in cubes if cube.startswith(test_prefix) or cube == submission
    ]

    for cube in clutter_cubes:
        logging.info(f"Removing clutter cube: {cube}")
        cube_path = os.path.join(cubes_path, cube)
        if os.path.exists(cube_path):
            try:
                if os.path.islink(cube_path):
                    os.unlink(cube_path)
                else:
                    rmtree(cube_path)
            except OSError as e:
                logging.error(f"Could not remove cube {cube}: {e}")
                config.ui.print_error(
                    f"Could not remove cube {cube}. For more information check the logs."
                )


def cleanup_benchmarks():
    """Removes clutter related to benchmarks
    """
    bmks_path = storage_path(config.benchmarks_storage)
    bmks = os.listdir(bmks_path)
    clutter_bmks = [bmk for bmk in bmks if bmk.startswith(config.tmp_prefix)]

    for bmk in clutter_bmks:
        logging.info(f"Removing clutter benchmark: {bmk}")
        bmk_path = os.path.join(bmks_path, bmk)
        if os.path.exists(bmk_path):
            try:
                rmtree(bmk_path)
            except OSError as e:
                logging.error(f"Could not remove benchmark {bmk}: {e}")
                config.ui.print_error(
                    f"Could not remove benchmark {bmk}. For more information check the logs."
                )


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


def pretty_error(msg: str, ui: "UI", clean: bool = True, add_instructions=True):
    """Prints an error message with typer protocol and exits the script

    Args:
        msg (str): Error message to show to the user
        clean (bool, optional):
            Run the cleanup process before exiting. Defaults to True.
        add_instructions (bool, optional):
            Show additional instructions to the user. Defualts to True.
    """
    logging.warning(
        "MedPerf had to stop execution. See logs above for more information"
    )
    if msg[-1] != ".":
        msg = msg + "."
    if add_instructions:
        msg += f" See logs at {config.log_file} for more information"
    ui.print_error(msg)
    if clean:
        cleanup()
    sys.exit(1)


def cube_path(uid: int) -> str:
    """Gets the path for a given cube.

    Args:
        uid (int): Cube UID.

    Returns:
        str: Location of the cube folder structure.
    """
    return os.path.join(storage_path(config.cubes_storage), str(uid))


def generate_tmp_datapath() -> Tuple[str, str]:
    """Builds a temporary folder for prepared but yet-to-register datasets.

    Returns:
        str: General temporary folder location
        str: Specific data path for the temporary dataset
    """
    uid = generate_tmp_uid()
    tmp = config.tmp_prefix + uid
    out_path = os.path.join(storage_path(config.data_storage), tmp)
    out_path = os.path.abspath(out_path)
    return out_path


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


def check_cube_validity(cube: "Cube", ui: "UI"):
    """Helper function for pretty printing the cube validity process.

    Args:
        cube (Cube): Cube to check for validity
        ui (UI): Instance of an UI implementation
    """
    logging.info(f"Checking cube {cube.name} validity")
    ui.text = "Checking cube MD5 hash..."
    if not cube.is_valid():
        pretty_error("MD5 hash doesn't match", ui)
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


def approval_prompt(msg: str, ui: "UI") -> bool:
    """Helper function for prompting the user for things they have to explicitly approve.

    Args:
        msg (str): What message to ask the user for approval.

    Returns:
        bool: Wether the user explicitly approved or not.
    """
    logging.info("Prompting for user's approval")
    approval = None
    while approval is None or approval not in "yn":
        approval = ui.prompt(msg.strip() + " ").lower()
    logging.info(f"User answered approval with {approval}")
    return approval == "y"


def dict_pretty_print(in_dict: dict, ui: "UI"):
    """Helper function for distinctively printing dictionaries with yaml format.

    Args:
        in_dict (dict): dictionary to print
    """
    logging.debug(f"Printing dictionary to the user: {in_dict}")
    ui.print()
    ui.print("=" * 20)
    in_dict = {k: v for (k, v) in in_dict.items() if v is not None}
    ui.print(yaml.dump(in_dict))
    logging.debug(f"Dictionary printed to the user: {in_dict}")
    ui.print("=" * 20)


def combine_proc_sp_text(proc: spawn, ui: "UI") -> str:
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
    static_text = ui.text
    proc_out = ""
    while proc.isalive():
        try:
            line = byte = proc.read(1)
        except TIMEOUT:
            logging.info("Process timed out")
            pretty_error("Process timed out", ui)

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


def results_path(benchmark_uid, model_uid, data_uid):
    out_path = storage_path(config.results_storage)
    bmark_uid = str(benchmark_uid)
    model_uid = str(model_uid)
    data_uid = str(data_uid)
    out_path = os.path.join(out_path, bmark_uid, model_uid, data_uid)
    out_path = os.path.join(out_path, config.results_filename)
    return out_path


def results_ids(ui: UI):
    results_storage = storage_path(config.results_storage)
    logging.debug("Getting results ids")
    results_ids = []
    try:
        bmk_uids = next(os.walk(results_storage))[1]
        for bmk_uid in bmk_uids:
            bmk_storage = os.path.join(results_storage, bmk_uid)
            model_uids = next(os.walk(bmk_storage))[1]
            for model_uid in model_uids:
                bmk_model_storage = os.path.join(bmk_storage, model_uid)
                data_uids = next(os.walk(bmk_model_storage))[1]
                bmk_model_data_list = [
                    (bmk_uid, model_uid, data_uid) for data_uid in data_uids
                ]
                results_ids += bmk_model_data_list

    except StopIteration:
        msg = "Couldn't iterate over the results directory"
        logging.warning(msg)
        pretty_error(msg, ui)
    logging.debug(f"Results ids: {results_ids}")
    return results_ids


def setup_logger(logger, log_lvl):
    fh = logging.FileHandler(config.log_file)
    fh.setLevel(log_lvl)
    logger.addHandler(fh)


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


def save_cube_metadata(meta, local_hashes):
    c_path = cube_path(meta["id"])
    if not os.path.isdir(c_path):
        os.makedirs(c_path, exist_ok=True)
    meta_file = os.path.join(c_path, config.cube_metadata_filename)
    with open(meta_file, "w") as f:
        yaml.dump(meta, f)
    local_hashes_file = os.path.join(c_path, config.cube_hashes_filename)
    with open(local_hashes_file, "w") as f:
        yaml.dump(local_hashes, f)


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
