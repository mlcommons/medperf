from __future__ import annotations

import re
import os
import sys
import yaml
import random
import hashlib
import logging
import tarfile
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
from medperf.exceptions import ExecutionError, InvalidEntityError, MedperfException


def storage_path(subpath: str):
    """Helper function that converts a path to storage-related path"""
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


def set_unique_tmp_config():
    """Set current process' temporary unique names
    Enables simultaneous execution without cleanup collision
    """
    pid = str(os.getpid())
    config.tmp_storage += pid
    config.tmp_prefix += pid
    config.test_dset_prefix += pid
    config.test_cube_prefix += pid
    config.cube_submission_id += pid


def cleanup(extra_paths: List[str] = []):
    """Removes clutter and unused files from the medperf folder structure.
    """
    if not config.cleanup:
        logging.info("Cleanup disabled")
        return
    tmp_path = storage_path(config.tmp_storage)
    extra_paths.append(tmp_path)
    for path in extra_paths:
        if os.path.exists(path):
            logging.info(f"Removing clutter path: {path}")
            try:
                rmtree(path)
            except OSError as e:
                logging.error("Could not remove clutter path")
                raise MedperfException(str(e))

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
                logging.error(f"Could not remove dataset {dset}")
                raise MedperfException(str(e))


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
                logging.error(f"Could not remove cube {cube}")
                raise MedperfException(str(e))


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
                logging.error(f"Could not remove benchmark {bmk}")
                raise MedperfException(str(e))


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


def pretty_error(msg: str, clean: bool = True, add_instructions=True):
    """Prints an error message with typer protocol and exits the script

    Args:
        msg (str): Error message to show to the user
        clean (bool, optional):
            Run the cleanup process before exiting. Defaults to True.
        add_instructions (bool, optional):
            Show additional instructions to the user. Defualts to True.
    """
    ui = config.ui
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


def check_cube_validity(cube: "Cube"):
    """Helper function for pretty printing the cube validity process.

    Args:
        cube (Cube): Cube to check for validity
        ui (UI): Instance of an UI implementation
    """
    logging.info(f"Checking cube {cube.name} validity")
    ui = config.ui
    ui.text = "Checking cube MD5 hash..."
    if not cube.is_valid():
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


def dict_pretty_print(in_dict: dict):
    """Helper function for distinctively printing dictionaries with yaml format.

    Args:
        in_dict (dict): dictionary to print
    """
    logging.debug(f"Printing dictionary to the user: {in_dict}")
    ui = config.ui
    ui.print()
    ui.print("=" * 20)
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


def results_path(benchmark_uid, model_uid, data_uid):
    out_path = storage_path(config.results_storage)
    bmark_uid = str(benchmark_uid)
    model_uid = str(model_uid)
    data_uid = str(data_uid)
    out_path = os.path.join(out_path, bmark_uid, model_uid, data_uid)
    return out_path


def results_ids():
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
        raise MedperfException(msg)
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
