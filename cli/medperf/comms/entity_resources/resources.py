"""haha"""

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
    """Downloads and writes an mlcube.yaml file from the server

    Args:
        url (str): URL where the mlcube.yaml file can be downloaded.
        cube_path (str): Cube location.

    Returns:
        str: location where the mlcube.yaml file is stored locally.
    """
    output_path = os.path.join(cube_path, config.cube_filename)
    hash = download_resource(url, output_path, expected_hash)
    return output_path, hash


def get_cube_params(url: str, cube_path: str, expected_hash: str = None) -> str:
    """Retrieves the cube parameters.yaml file from the server

    Args:
        url (str): URL where the parameters.yaml file can be downloaded.
        cube_path (str): Cube location.

    Returns:
        str: Location where the parameters.yaml file is stored locally.
    """
    output_path = os.path.join(cube_path, config.workspace_path, config.params_filename)
    hash = download_resource(url, output_path, expected_hash)
    return output_path, hash


def get_cube_image(url: str, cube_path: str, hash_value: str = None) -> str:
    """Retrieves and stores the image file from the server. Stores images
    on a shared location, and retrieves a cached image by hash if found locally.
    Creates a symbolic link to the cube storage.

    Args:
        url (str): URL where the image file can be downloaded.
        cube_path (str): Path to cube.
        hash (str, Optional): File hash to store under shared storage. Defaults to None.

    Returns:
        str: Location where the image file is stored locally.
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
    """Retrieves and stores the additional_files.tar.gz file from the server

    Note: there is no scenario of having expected_tarball_hash == None and
    expected_folder_hash != None, since passing the expected_folder_hash is
    something controlled by the client not the user. If the client has
    expected_tarball_hash == None, then there is no way the client has
    expected_folder_hash != None.

    Args:
        url (str): URL where the additional_files.tar.gz file can be downloaded.
        cube_path (str): Cube location.

    Returns:
        str: Location where the additional_files.tar.gz file is stored locally.
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
    """Downloads the benchmark demo dataset and stores it in the user's machine

    Args:
        demo_data_url (str): location of demo data for download
        uid (str): UID to use for storing the demo dataset. Defaults to generate_tmp_uid().

    Returns:
        str: path where the downloaded demo dataset can be found
    """
    demo_storage = storage_path(config.demo_data_storage)
    if expected_hash:
        demo_dataset_folder = os.path.join(demo_storage, expected_hash)
        output_path = os.path.join(demo_dataset_folder, config.tarball_filename)
        if not os.path.exists(output_path):
            # first, handle the possibility of having clutter uncompressed files
            remove_path(demo_dataset_folder)
            download_resource(url, output_path, expected_hash)
    else:
        tmp_output_path = generate_tmp_path()
        expected_hash = download_resource(url, tmp_output_path)
        demo_dataset_folder = os.path.join(demo_storage, expected_hash)
        output_path = os.path.join(demo_dataset_folder, config.tarball_filename)
        # first, handle the possibility of having clutter uncompressed files
        remove_path(demo_dataset_folder)
        os.makedirs(demo_dataset_folder)
        os.rename(tmp_output_path, output_path)

    return output_path, expected_hash
