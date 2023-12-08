from medperf.utils import storage_path, get_folders_hash
from medperf.exceptions import InvalidArgumentError, InvalidEntityError

from medperf.comms.entity_resources import resources
from medperf.entities.cube import Cube
import medperf.config as config
import os
import yaml
from pathlib import Path
import logging


def download_demo_data(dset_url, dset_hash):
    """Retrieves the demo dataset associated to the specified benchmark

    Returns:
        data_path (str): Location of the downloaded data
        labels_path (str): Location of the downloaded labels
    """
    try:
        demo_dset_path, _ = resources.get_benchmark_demo_dataset(dset_url, dset_hash)
    except InvalidEntityError as e:
        raise InvalidEntityError(f"Demo dataset {dset_url}: {e}")

    # It is assumed that all demo datasets contain a file
    # which specifies the input of the data preparation step
    paths_file = os.path.join(demo_dset_path, config.demo_dset_paths_file)
    with open(paths_file, "r") as f:
        paths = yaml.safe_load(f)

    data_path = os.path.join(demo_dset_path, paths["data_path"])
    labels_path = os.path.join(demo_dset_path, paths["labels_path"])
    return data_path, labels_path


def prepare_local_cube(path):
    temp_uid = get_folders_hash([path])
    cubes_storage = storage_path(config.cubes_storage)
    dst = os.path.join(cubes_storage, temp_uid)
    os.symlink(path, dst)
    logging.info(f"local cube will be linked to path: {dst}")
    config.tmp_paths.append(dst)
    cube_metadata_file = os.path.join(path, config.cube_metadata_filename)
    if not os.path.exists(cube_metadata_file):
        temp_metadata = {
            "id": None,
            "name": temp_uid,
            "git_mlcube_url": "mock_url",
            "mlcube_hash": "",
            "parameters_hash": "",
            "image_tarball_hash": "",
            "additional_files_tarball_hash": "",
            "for_test": True,
        }
        metadata = Cube(**temp_metadata).todict()
        with open(cube_metadata_file, "w") as f:
            yaml.dump(metadata, f)
        config.tmp_paths.append(cube_metadata_file)

    return temp_uid


def prepare_cube(cube_uid: str):
    """Assigns the attr used for testing according to the initialization parameters.
    If the value is a path, it will create a temporary uid and link the cube path to
    the medperf storage path.

    Arguments:
        attr (str): Attribute to check and/or reassign.
        fallback (any): Value to assign if attribute is empty. Defaults to None.
    """

    # Test if value looks like an mlcube_uid, if so skip path validation
    if str(cube_uid).isdigit():
        logging.info(f"MLCube value {cube_uid} resembles an mlcube_uid")
        return cube_uid

    # Check if value is a local mlcube
    path = Path(cube_uid)
    if path.is_file():
        path = path.parent
    path = path.resolve()

    if os.path.exists(path):
        logging.info("local path provided. Creating symbolic link")
        temp_uid = prepare_local_cube(path)
        return temp_uid

    logging.error(f"mlcube {cube_uid} was not found as an existing mlcube")
    raise InvalidArgumentError(
        f"The provided mlcube ({cube_uid}) could not be found as a local or remote mlcube"
    )


def get_cube(uid: int, name: str, local_only: bool = False) -> Cube:
    config.ui.text = f"Retrieving {name} cube"
    cube = Cube.get(uid, local_only=local_only)
    config.ui.print(f"> {name} cube download complete")
    return cube
