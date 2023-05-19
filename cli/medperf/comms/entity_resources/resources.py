"""This module downloads files from the internet. It provides a set of
functions to download common files that are necessary for workflow executions
and are not on the MedPerf server. An example of such files is model weights
of a Model MLCube.

This module takes care of validating the integrity of the downloaded file
if a hash was specified when requesting the file. It also returns the hash
of the downloaded file, which can be the original specified hash or the
calculated hash of the freshly downloaded file if no hash was specified.

Additionally, to avoid unnecessary downloads, an existing file with
a valid integrity will not be re-downloaded.
"""

import shutil
import os
import medperf.config as config
from medperf.utils import (
    base_storage_path,
    generate_tmp_path,
    get_cube_image_name,
    get_folder_sha1,
    remove_path,
    storage_path,
    untar,
)
from .utils import download_resource


def get_cube(url: str, cube_path: str, expected_hash: str = None) -> str:
    """Downloads and writes an mlcube.yaml file. If the hash is provided,
    the downloaded file's integrity will be checked.

    Args:
        url (str): URL where the mlcube.yaml file can be downloaded.
        cube_path (str): Cube location.
        expected_hash (str, optional): expected sha1 hash of the downloaded file

    Returns:
        output_path (str): location where the mlcube.yaml file is stored locally.
        hash_value (str): The hash of the downloaded file
    """
    output_path = os.path.join(cube_path, config.cube_filename)
    hash_value = download_resource(url, output_path, expected_hash)
    return output_path, hash_value


def get_cube_params(url: str, cube_path: str, expected_hash: str = None) -> str:
    """Downloads and writes a cube parameters file. If the hash is provided,
    the downloaded file's integrity will be checked.

    Args:
        url (str): URL where the parameters.yaml file can be downloaded.
        cube_path (str): Cube location.
        expected_hash (str, optional): expected sha1 hash of the downloaded file

    Returns:
        output_path (str): location where the parameters file is stored locally.
        hash_value (str): The hash of the downloaded file
    """
    output_path = os.path.join(cube_path, config.workspace_path, config.params_filename)
    hash_value = download_resource(url, output_path, expected_hash)
    return output_path, hash_value


def get_cube_image(url: str, cube_path: str, hash_value: str = None) -> str:
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
    image_path = config.image_path
    image_name = get_cube_image_name(cube_path)
    image_cube_path = os.path.join(cube_path, image_path)
    os.makedirs(image_cube_path, exist_ok=True)
    image_cube_file = os.path.join(image_cube_path, image_name)
    if os.path.exists(image_cube_file):
        # Remove existing links
        os.unlink(image_cube_file)

    imgs_storage = base_storage_path(config.images_storage)
    if not hash_value:
        # No hash provided, we need to download the file first
        hash_value = download_resource(url, image_cube_file)
        img_storage = os.path.join(imgs_storage, hash_value)
        shutil.move(image_cube_file, img_storage)
    else:
        img_storage = os.path.join(imgs_storage, hash_value)
        if not os.path.exists(img_storage):
            # If image doesn't exist locally, download it normally
            download_resource(url, img_storage, hash_value)

    # Create a symbolic link to individual cube storage
    os.symlink(img_storage, image_cube_file)
    return image_cube_file, hash_value


def get_cube_additional(
    url: str,
    cube_path: str,
    expected_tarball_hash: str = None,
    expected_folder_hash: str = None,
) -> str:
    """Retrieves additional files of an MLCube. The additional files
    will be in a compressed tarball file. The function will extract this
    file and returns the hash of its contents.

    Note: there is no scenario of having `expected_tarball_hash == None` and
    `expected_folder_hash != None` at the same time, since passing the
    expected_folder_hash is something controlled by the client not the user.
    If the client had `expected_tarball_hash == None`, then there is no way the
    client would have expected_folder_hash != None.

    Args:
        url (str): URL where the additional_files.tar.gz file can be downloaded.
        cube_path (str): Cube location.
        expected_tarball_hash (str, optional): expected sha1 hash of tarball file
        expected_folder_hash (str, optional): expected sha1 hash of uncompressed
        version of the tarball file

    Returns:
        tarball_hash (str): The hash of the downloaded file
        folder_hash (str): The hash of the uncompressed version of the downloaded file
    """
    additional_files_folder = os.path.join(cube_path, config.additional_path)

    # If the additional_files folder exists, check if it has the expected hash
    if expected_folder_hash and os.path.exists(additional_files_folder):
        folder_hash = get_folder_sha1(additional_files_folder)
        if folder_hash == expected_folder_hash:
            return expected_tarball_hash, expected_folder_hash

    # Remove the folder if it exists
    remove_path(additional_files_folder)

    # Download the tarball file as usual
    output_path = os.path.join(additional_files_folder, config.tarball_filename)
    tarball_hash = download_resource(url, output_path, expected_tarball_hash)

    # Untar and keep track of the folder hash.
    untar(output_path)
    folder_hash = get_folder_sha1(additional_files_folder)
    return tarball_hash, folder_hash


def get_benchmark_demo_dataset(url: str, expected_hash: str = None) -> str:
    """Downloads and writes a demo dataset. If the hash is provided,
    the downloaded file's integrity will be checked.

    Args:
        url (str): URL where the compressed demo dataset file can be downloaded.
        expected_hash (str, optional): expected sha1 hash of the downloaded file

    Returns:
        output_path (str): location where the compressed demo dataset file is stored locally.
        hash_value (str): The hash of the downloaded file
    """
    # TODO: at some point maybe it is better to download demo datasets in
    # their benchmark folder. Doing this, we should then modify
    # the compatibility test command and remove the option of directly passing
    # demo datasets. This would look cleaner.
    demo_storage = storage_path(config.demo_data_storage)
    if expected_hash:
        demo_dataset_folder = os.path.join(demo_storage, expected_hash)
        output_path = os.path.join(demo_dataset_folder, config.tarball_filename)
        if not os.path.exists(output_path):
            # first, handle the possibility of having clutter uncompressed files
            remove_path(demo_dataset_folder)
            download_resource(url, output_path, expected_hash)
        hash_value = expected_hash
    else:
        tmp_output_path = generate_tmp_path()
        hash_value = download_resource(url, tmp_output_path)
        demo_dataset_folder = os.path.join(demo_storage, hash_value)
        output_path = os.path.join(demo_dataset_folder, config.tarball_filename)
        # first, handle the possibility of having clutter uncompressed files
        remove_path(demo_dataset_folder)
        os.makedirs(demo_dataset_folder)
        os.rename(tmp_output_path, output_path)

    return output_path, hash_value
