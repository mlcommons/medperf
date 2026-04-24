from medperf.commands.dataset.prepare import DataPreparation
from medperf.commands.dataset.submit import DataCreation
from medperf.utils import get_folders_hash, remove_path, store_decryption_key
from medperf.exceptions import InvalidEntityError
from medperf.entities.model import Model
from medperf.comms.entity_resources import resources
from medperf.entities.cube import Cube
import medperf.config as config
import os
import yaml
import logging
from medperf.enums import ModelType


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


def prepare_model(model_uid: str, decryption_key_file_path: os.PathLike = None):
    model = Model.get(model_uid)
    if model.type == ModelType.CONTAINER.value:
        # execution later will download run files if needed
        setup_cube(model.container_obj, decryption_key_file_path, download=False)
    return model


def prepare_cube(cube_uid: str, decryption_key_file_path: os.PathLike = None):
    cube = Cube.get(cube_uid)
    return setup_cube(cube, decryption_key_file_path)


def setup_cube(
    cube: Cube, decryption_key_file_path: os.PathLike = None, download=True
) -> Cube:

    if decryption_key_file_path is not None:
        logging.debug(f"Model decryption key is provided: {decryption_key_file_path}")
        decryption_key_path = store_decryption_key(
            cube.identifier, decryption_key_file_path
        )
        config.sensitive_tmp_paths.append(decryption_key_path)

    if download:
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
