from pexpect import spawn
import logging
from yaspin.core import Yaspin
from typing import List, Tuple
from datetime import datetime
import hashlib
import os
from shutil import rmtree
import tarfile
import typer
import yaml
from pathlib import Path
from colorama import Fore, Style
import re

from medperf.config import config


def get_file_sha1(path: str) -> str:
    """Calculates the sha1 hash for a given file.

    Args:
        path (str): Location of the file of interest.

    Returns:
        str: Calculated hash
    """
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()
    with open(path, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)

    return sha1.hexdigest()


def init_storage():
    """Builds the general medperf folder structure.
    """
    parent = config["storage"]
    data = config["data_storage"]
    cubes = config["cubes_storage"]
    results = config["results_storage"]
    tmp = config["tmp_storage"]

    dirs = [parent, data, cubes, results, tmp]
    for dir in dirs:
        if not os.path.isdir(dir):
            logging.info(f"Creating {dir} directory")
            os.mkdir(dir)


def cleanup():
    """Removes clutter and unused files from the medperf folder structure.
    """
    if os.path.exists(config["tmp_storage"]):
        logging.info("Removing temporary data storage")
        rmtree(config["tmp_storage"], ignore_errors=True)
    dsets = get_dsets()
    prefix = config["tmp_reg_prefix"]
    unreg_dsets = [dset for dset in dsets if dset.startswith(prefix)]
    for dset in unreg_dsets:
        logging.info("Removing unregistered dataset")
        dset_path = os.path.join(config["data_storage"], dset)
        if os.path.exists(dset_path):
            rmtree(dset_path, ignore_errors=True)


def get_dsets() -> List[str]:
    """Retrieves the UID of all the datasets stored locally.

    Returns:
        List[str]: UIDs of prepared datasets.
    """
    data = config["data_storage"]
    dsets_path = os.path.join(config["storage"], data)
    dsets = next(os.walk(dsets_path))[1]
    return dsets


def pretty_error(msg: str, clean: bool = True, add_instructions=True):
    """Prints an error message with typer protocol and exits the script

    Args:
        msg (str): Error message to show to the user
        clean (bool, optional): Wether to run the cleanup process before exiting. Defaults to True.
        add_instructions (bool, optional): Wether to show additional instructions to the user. Defualts to True.
    """
    logging.warning(
        "MedPerf had to stop execution. See logs above for more information"
    )
    if msg[-1] != ".":
        msg = msg + "."
    msg = f"❌ {msg}"
    if add_instructions:
        msg += f" See logs at {config['log_file']} for more information"
    msg = typer.style(msg, fg=typer.colors.RED, bold=True)
    typer.echo(msg)
    if clean:
        cleanup()
    exit()


def cube_path(uid: int) -> str:
    """Gets the path for a given cube.

    Args:
        uid (int): Cube UID.

    Returns:
        str: Location of the cube folder structure.
    """
    return os.path.join(config["storage"], "cubes", str(uid))


def generate_tmp_datapath() -> Tuple[str, str]:
    """Builds a temporary folder for prepared but yet-to-register datasets.

    Returns:
        str: General temporary folder location
        str: Specific data path for the temporary dataset
    """
    dt = datetime.now()
    ts = str(int(datetime.timestamp(dt)))
    tmp = config["tmp_reg_prefix"] + ts
    out_path = os.path.join(config["storage"], "data", tmp)
    out_path = os.path.abspath(out_path)
    out_datapath = os.path.join(out_path, "data")
    if not os.path.isdir(out_datapath):
        logging.info(f"Creating temporary dataset path: {out_datapath}")
        os.makedirs(out_datapath)
    return out_path, out_datapath


def check_cube_validity(cube: "Cube", sp: Yaspin):
    """Helper function for pretty printing the cube validity process.

    Args:
        cube (Cube): Cube to check for validity
        sp (Yaspin): yaspin instance being used
    """
    logging.info(f"Checking cube {cube.name} validity")
    sp.text = "Checking cube MD5 hash..."
    if not cube.is_valid():
        pretty_error("MD5 hash doesn't match")
    logging.info(f"Cube {cube.name} is valid")
    sp.write(f"> {cube.name} MD5 hash check complete")


def untar_additional(add_filepath: str) -> str:
    """Untars and removes the additional_files.tar.gz file

    Args:
        add_filepath (str): Path where the additional_files.tar.gz file can be found.

    Returns:
        str: location where the untared files can be found.
    """
    logging.info(f"Uncompressing additional_files.tar.gz at {add_filepath}")
    addpath = str(Path(add_filepath).parent)
    tar = tarfile.open(add_filepath)
    tar.extractall(addpath)
    tar.close()
    os.remove(add_filepath)
    return addpath


def approval_prompt(msg: str) -> bool:
    """Helper function for prompting the user for things they have to explicitly approve.

    Args:
        msg (str): What message to ask the user for approval.

    Returns:
        bool: Wether the user explicitly approved or not.
    """
    logging.info("Prompting for user's approval")
    approval = None
    while approval is None or approval not in "yn":
        approval = input(msg.strip() + " ").lower()
    logging.info(f"User answered approval with {approval}")
    return approval == "y"


def dict_pretty_print(in_dict: dict):
    """Helper function for distinctively printing dictionaries with yaml format.

    Args:
        in_dict (dict): dictionary to print
    """
    logging.debug(f"Printing dictionary to the user: {in_dict}")
    typer.echo()
    typer.echo("=" * 20)
    in_dict = {k: v for (k, v) in in_dict.items() if v is not None}
    typer.echo(yaml.dump(in_dict))
    typer.echo("=" * 20)


def combine_proc_sp_text(proc: spawn, sp: Yaspin) -> str:
    """Combines the output of a process and the spinner. 
    Joins any string captured from the process with the 
    spinner current text. Any strings ending with any other 
    character from the subprocess will be returned later.

    Args:
        proc (spawn): a pexpect spawned child
        sp (Yaspin): a Yaspin spinner

    Returns:
        str: all non-carriage-return-ending string captured from proc
    """
    static_text = sp.text
    proc_out = ""
    while proc.isalive():
        line = byte = proc.read(1)
        while byte and not re.match(b"[\r\n]", byte):
            byte = proc.read(1)
            line += byte
        if not byte:
            break
        line = line.decode("utf-8", "ignore")
        if line:
            # add to proc_out list for logging
            proc_out += line
        sp.text = (
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
            filepath = os.path.join(root, file)
            hashes.append(get_file_sha1(filepath))

    hashes = sorted(hashes)
    sha1 = hashlib.sha1()
    for hash in hashes:
        sha1.update(hash.encode("utf-8"))
    return sha1.hexdigest()

