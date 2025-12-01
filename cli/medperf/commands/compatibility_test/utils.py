from medperf.commands.dataset.prepare import DataPreparation
from medperf.commands.dataset.submit import DataCreation
from medperf.utils import (
    generate_tmp_path,
    get_folders_hash,
    sanitize_path,
    remove_path,
    generate_tmp_uid,
    store_decryption_key,
)
from medperf.exceptions import InvalidArgumentError, InvalidEntityError

from medperf.comms.entity_resources import resources
from medperf.entities.cube import Cube
import medperf.config as config
import os
import yaml
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


def prepare_local_cube(container_config_path, parameters=None, additional=None):
    parameters_config = None
    if parameters is not None:
        with open(parameters, "r") as f:
            parameters_config = yaml.safe_load(f)
    with open(container_config_path, "r") as f:
        container_config = yaml.safe_load(f)

    temp_metadata = {
        "id": None,
        "name": "local_" + generate_tmp_uid(),
        "container_config": container_config,
        "parameters_config": parameters_config,
        "image_tarball_hash": "",
        "additional_files_tarball_hash": "",
        "for_test": True,
    }
    cube = Cube(**temp_metadata)
    cube.params_path = generate_tmp_path()
    if additional is not None:
        cube.additional_files_folder_path = additional

    return cube


def prepare_cube(
    cube_uid: str,
    parameters: str = None,
    additional: str = None,
    local_only: bool = False,
    use_local_container_image: bool = False,
    decryption_key_file_path: os.PathLike = None,
):

    # Test if value looks like an mlcube_uid, if so skip path validation
    if str(cube_uid).isdigit():
        logging.info(f"Container identifier {cube_uid} resembles a server ID")
        cube = Cube.get(cube_uid, local_only=local_only)
        return setup_cube(cube, use_local_container_image, decryption_key_file_path)

    # Check if value is a local mlcube
    path = sanitize_path(cube_uid)

    if os.path.isfile(path):
        logging.info("local path provided. Preparing local container")
        tmp_cube = prepare_local_cube(path, parameters, additional)
        return setup_cube(tmp_cube, use_local_container_image, decryption_key_file_path)

    logging.error(f"container {cube_uid} was not found")
    raise InvalidArgumentError(
        f"The provided container ({cube_uid}) could not be found as a local or remote container"
    )


def setup_cube(
    cube: Cube,
    use_local_container_image: bool = False,
    decryption_key_file_path: os.PathLike = None,
) -> Cube:

    if decryption_key_file_path is not None:
        logging.debug(f"Model decryption key is provided: {decryption_key_file_path}")
        decryption_key_path = store_decryption_key(
            cube.identifier, decryption_key_file_path
        )
        config.sensitive_tmp_paths.append(decryption_key_path)

    if not use_local_container_image:
        logging.debug("Downloading container run files")
        cube.download_run_files()
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
        prep_cube_uid=data_prep_mlcube.identifier,
        data_path=data_path,
        labels_path=labels_path,
        metadata_path=metadata_path,
        name="demo_data",
        description="demo_data",
        location="local",
        approved=False,
        submit_as_prepared=skip_data_preparation_step,
        for_test=True,
    )
    data_creation.validate()
    data_creation.create_dataset_object()

    # make some changes since this is a test dataset
    remove_path(data_creation.dataset.data_path)
    remove_path(data_creation.dataset.labels_path)
    remove_path(data_creation.dataset.metadata_path)
    remove_path(data_creation.dataset.report_path)
    remove_path(data_creation.dataset.statistics_path)
    config.tmp_paths.remove(data_creation.dataset.path)
    if skip_data_preparation_step:
        data_creation.make_dataset_prepared()
    dataset = data_creation.dataset
    old_generated_uid = dataset.generated_uid
    old_path = dataset.path

    # prepare/check dataset
    DataPreparation.run(dataset.generated_uid, data_preparation_cube=data_prep_mlcube)

    # update dataset generated_uid
    new_generated_uid = get_folders_hash([dataset.data_path, dataset.labels_path])
    if new_generated_uid != old_generated_uid:
        # move to a correct location if it underwent preparation
        new_path = old_path.replace(old_generated_uid, new_generated_uid)
        remove_path(new_path)
        os.rename(old_path, new_path)
        dataset.generated_uid = new_generated_uid
        dataset.write()

    return new_generated_uid
