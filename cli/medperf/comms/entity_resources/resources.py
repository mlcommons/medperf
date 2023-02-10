import shutil
import os
import medperf.config as config
from medperf.utils import (
    base_storage_path,
    get_file_sha1,
    storage_path,
    generate_tmp_uid,
)
from .utils import download_resource


def __get_cube_file(url: str, cube_path: str, path: str, filename: str):
    path = os.path.join(cube_path, path)
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, filename)
    download_resource(url, filepath)
    hash = get_file_sha1(filepath)
    return filepath, hash


def get_cube(url: str, cube_path: str) -> str:
    """Downloads and writes an mlcube.yaml file from the server

    Args:
        url (str): URL where the mlcube.yaml file can be downloaded.
        cube_path (str): Cube location.

    Returns:
        str: location where the mlcube.yaml file is stored locally.
    """
    cube_file = config.cube_filename
    return __get_cube_file(url, cube_path, "", cube_file)


def get_cube_params(url: str, cube_path: str) -> str:
    """Retrieves the cube parameters.yaml file from the server

    Args:
        url (str): URL where the parameters.yaml file can be downloaded.
        cube_path (str): Cube location.

    Returns:
        str: Location where the parameters.yaml file is stored locally.
    """
    ws = config.workspace_path
    params_file = config.params_filename
    return __get_cube_file(url, cube_path, ws, params_file)


def get_cube_image(url: str, cube_path: str, hash: str = None) -> str:
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
    image_name = url.split("/")[-1]  # Get the last part of the URL path
    image_name = image_name.split("?")[0]  # Remove query parameters
    image_cube_path = os.path.join(cube_path, image_path)
    os.makedirs(image_cube_path, exist_ok=True)
    image_cube_file = os.path.join(image_cube_path, image_name)
    imgs_storage = base_storage_path(config.images_storage)

    if not hash:
        # No hash provided, we need to download the file first
        _, local_hash = __get_cube_file(url, cube_path, image_path, image_name)
        img_storage = os.path.join(imgs_storage, local_hash)
        shutil.move(image_cube_file, img_storage)
    else:
        img_storage = os.path.join(imgs_storage, hash)

    if not os.path.exists(img_storage):
        # If image doesn't exist locally, download it normally
        # And move it to shared storage
        _, local_hash = __get_cube_file(url, cube_path, image_path, image_name)
        shutil.move(image_cube_file, img_storage)

    # Create a symbolic link to individual cube storage
    if os.path.exists(image_cube_file):
        # Remove existing links
        os.unlink(image_cube_file)
    os.symlink(img_storage, image_cube_file)
    local_hash = get_file_sha1(img_storage)
    return image_cube_file, local_hash


def get_cube_additional(url: str, cube_path: str) -> str:
    """Retrieves and stores the additional_files.tar.gz file from the server

    Args:
        url (str): URL where the additional_files.tar.gz file can be downloaded.
        cube_path (str): Cube location.

    Returns:
        str: Location where the additional_files.tar.gz file is stored locally.
    """
    add_path = config.additional_path
    tball_file = config.tarball_filename
    return __get_cube_file(url, cube_path, add_path, tball_file)


def get_benchmark_demo_dataset(
    demo_data_url: str, uid: str = generate_tmp_uid()
) -> str:
    """Downloads the benchmark demo dataset and stores it in the user's machine

    Args:
        demo_data_url (str): location of demo data for download
        uid (str): UID to use for storing the demo dataset. Defaults to generate_tmp_uid().

    Returns:
        str: path where the downloaded demo dataset can be found
    """
    tmp_dir = storage_path(config.demo_data_storage)
    demo_data_path = os.path.join(tmp_dir, uid)
    tball_file = config.tarball_filename
    filepath = os.path.join(demo_data_path, tball_file)

    # Don't re-download if something already exists with same uid
    if os.path.exists(filepath):
        return filepath

    os.makedirs(demo_data_path, exist_ok=True)

    download_resource(demo_data_url, filepath)
    return filepath
