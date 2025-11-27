"""This module downloads files from the internet. It provides a set of
functions to download common files that are necessary for workflow executions
and are not on the MedPerf server. An example of such files is model weights
of a Model MLCube.

This module takes care of validating the integrity of the downloaded file
if a hash was specified when requesting the file. It also returns the hash
of the downloaded file, which can be the original specified hash or the
calculated hash of the freshly downloaded file if no hash was specified.

Additionally, to avoid unnecessary downloads, an existing file
will not be re-downloaded.
"""

import shutil
import os
import logging
import yaml
import medperf.config as config
from medperf.utils import generate_tmp_path, remove_path, untar, get_file_hash
from .utils import download_resource


def _should_get_regular_file(output_path, expected_hash):
    if os.path.exists(output_path) and expected_hash:
        calculated_hash = get_file_hash(output_path)
        logging.debug(
            f"{output_path}: Expected {expected_hash}, found {calculated_hash}."
        )
        if expected_hash == calculated_hash:
            logging.debug(f"{output_path} exists and is up to date")
            return False
        logging.debug(f"{output_path} exists but is out of date")
    return True


def _should_get_cube_additional(
    additional_files_folder, expected_tarball_hash, mlcube_local_cache_metadata
):
    # Read the hash of the tarball file whose extracted contents may already exist
    additional_files_cached_hash = None
    if os.path.exists(mlcube_local_cache_metadata):
        with open(mlcube_local_cache_metadata) as f:
            contents = yaml.safe_load(f)
        additional_files_cached_hash = contents.get(
            "additional_files_cached_hash", None
        )

    # Return if the additional files already exist and seem to originate from a valid tarball
    if os.path.exists(additional_files_folder) and expected_tarball_hash:
        if additional_files_cached_hash == expected_tarball_hash:
            logging.debug(f"{additional_files_folder} exists and is up to date")
            return False
        logging.debug(f"{additional_files_folder} exists but is out of date")
    return True


def _get_regular_file(url: str, output_path: str, expected_hash: str = None) -> str:
    """Downloads and writes a regular file. If the hash is provided,
    the file's integrity will be checked upon download.
    Used for parameters.yaml and mlcube.yaml

    Args:
        url (str): URL where the mlcube.yaml file can be downloaded.
        output_path (str): Path to store the downloaded file at.
        expected_hash (str, optional): expected hash of the downloaded file

    Returns:
        output_path (str): location where the regular file is stored locally.
        hash_value (str): The hash of the downloaded file
    """
    if not _should_get_regular_file(output_path, expected_hash):
        return output_path, expected_hash
    if os.path.exists(output_path):
        remove_path(output_path)
    hash_value = download_resource(url, output_path, expected_hash)
    return output_path, hash_value


def get_cube_image(url: str, hash_value: str = None) -> str:
    """Retrieves and stores the image file from the server. Stores images
    on a shared location, and retrieves a cached image by hash if found locally.
    Creates a symbolic link to the cube storage.

    Args:
        url (str): URL where the image file can be downloaded.
        cube_path (str): Path to cube.
        hash_value (str, Optional): File hash to store under shared storage. Defaults to None.

    Returns:
        image_cube_file: Location where the image file is stored locally.
        hash_value (str): The hash of the downloaded file
    """
    if hash_value:
        output_path = os.path.join(config.images_folder, hash_value)
        return _get_regular_file(url, output_path, hash_value)

    # No hash provided, we need to download the file
    tmp_output_path = generate_tmp_path()
    hash_value = download_resource(url, tmp_output_path)
    image_path = os.path.join(config.images_folder, hash_value)
    shutil.move(tmp_output_path, image_path)
    return image_path, hash_value


def get_cube_additional(
    url: str,
    cube_path: str,
    expected_tarball_hash: str = None,
) -> str:
    """Retrieves additional files of an MLCube. The additional files
    will be in a compressed tarball file. The function will additionally
    extract this file.

    Args:
        url (str): URL where the additional_files.tar.gz file can be downloaded.
        cube_path (str): Cube location.
        expected_tarball_hash (str, optional): expected hash of tarball file

    Returns:
        tarball_hash (str): The hash of the downloaded tarball file
    """
    additional_files_folder = os.path.join(cube_path, config.additional_path)
    mlcube_cache_file = os.path.join(cube_path, config.mlcube_cache_file)
    if not _should_get_cube_additional(
        additional_files_folder, expected_tarball_hash, mlcube_cache_file
    ):
        return additional_files_folder, expected_tarball_hash

    # Download the additional files. Make sure files are extracted in tmp storage
    # to avoid any clutter objects if uncompression fails for some reason.
    tmp_output_folder = generate_tmp_path()
    output_tarball_path = os.path.join(tmp_output_folder, config.tarball_filename)
    tarball_hash = download_resource(url, output_tarball_path, expected_tarball_hash)

    untar(output_tarball_path)
    parent_folder = os.path.dirname(os.path.normpath(additional_files_folder))
    os.makedirs(parent_folder, exist_ok=True)
    if os.path.exists(additional_files_folder):
        # handle the possibility of having clutter uncompressed files
        remove_path(additional_files_folder)
    os.rename(tmp_output_folder, additional_files_folder)

    # Store the downloaded tarball hash to be used later for verifying that the
    # local cache is up to date
    with open(mlcube_cache_file, "w") as f:  # assumes parent folder already exists
        contents = {"additional_files_cached_hash": tarball_hash}
        yaml.dump(contents, f)

    return additional_files_folder, tarball_hash


def get_benchmark_demo_dataset(url: str, expected_hash: str = None) -> str:
    """Downloads and extracts a demo dataset. If the hash is provided,
    the file's integrity will be checked upon download.

    Args:
        url (str): URL where the compressed demo dataset file can be downloaded.
        expected_hash (str, optional): expected hash of the downloaded file

    Returns:
        output_path (str): location where the uncompressed demo dataset is stored locally.
        hash_value (str): The hash of the downloaded tarball file
    """
    # TODO: at some point maybe it is better to download demo datasets in
    # their benchmark folder. Doing this, we should then modify
    # the compatibility test command and remove the option of directly passing
    # demo datasets. This would look cleaner.
    # Possible cons: if multiple benchmarks use the same demo dataset.
    demo_storage = config.demo_datasets_folder
    if expected_hash:
        # If the folder exists, return
        demo_dataset_folder = os.path.join(demo_storage, expected_hash)
        if os.path.exists(demo_dataset_folder):
            return demo_dataset_folder, expected_hash

    # make sure files are uncompressed while in tmp storage, to avoid any clutter
    # objects if uncompression fails for some reason.
    tmp_output_folder = generate_tmp_path()
    output_tarball_path = os.path.join(tmp_output_folder, config.tarball_filename)
    hash_value = download_resource(url, output_tarball_path, expected_hash)

    untar(output_tarball_path)
    demo_dataset_folder = os.path.join(demo_storage, hash_value)
    if os.path.exists(demo_dataset_folder):
        # handle the possibility of having clutter uncompressed files
        remove_path(demo_dataset_folder)
    os.rename(tmp_output_folder, demo_dataset_folder)
    return demo_dataset_folder, hash_value
