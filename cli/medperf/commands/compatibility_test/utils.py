from medperf.commands.dataset.prepare import DataPreparation
from medperf.commands.dataset.submit import DataCreation
from medperf.utils import get_folders_hash, remove_path
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
    metadata_path = None
    if "metadata_path" in paths:
        metadata_path = os.path.join(demo_dset_path, paths["metadata_path"])

    return data_path, labels_path, metadata_path


def prepare_local_cube(path):
    temp_uid = get_folders_hash([path])
    cubes_folder = config.cubes_folder
    dst = os.path.join(cubes_folder, temp_uid)
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
    cube.download_run_files()
    config.ui.print(f"> {name} cube download complete")
    return cube


def create_test_dataset(
    data_path,
    labels_path,
    metadata_path,
    data_prep_mlcube,
    skip_data_preparation_step: bool,
):
    # TODO: refactor this and write tests

    # create dataset object
    data_creation = DataCreation(
        benchmark_uid=None,
        prep_cube_uid=data_prep_mlcube,
        data_path=data_path,
        labels_path=labels_path,
        metadata_path=metadata_path,
        name="demo_data",
        description="demo_data",
        location="local",
        approved=False,
        submit_as_prepared=skip_data_preparation_step,
    )
    data_creation.validate()
    data_creation.create_dataset_object()
    # TODO: existing dataset could make problems
    # make some changes since this is a test dataset
    data_creation.dataset.for_test = True
    config.tmp_paths.remove(data_creation.dataset.path)
    data_creation.dataset.write()
    if skip_data_preparation_step:
        data_creation.make_dataset_prepared()
    dataset = data_creation.dataset

    # prepare/check dataset
    DataPreparation.run(dataset.generated_uid)

    # update dataset generated_uid
    old_path = dataset.path
    generated_uid = get_folders_hash([dataset.data_path, dataset.labels_path])
    dataset.generated_uid = generated_uid
    dataset.write()
    if dataset.input_data_hash != dataset.generated_uid:
        # move to a correct location if it underwent preparation
        new_path = old_path.replace(dataset.input_data_hash, generated_uid)
        remove_path(new_path)
        os.rename(old_path, new_path)

    return generated_uid
