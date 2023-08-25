import os
from medperf.utils import storage_path
from medperf import config
import yaml

from medperf.utils import get_file_hash
from medperf.exceptions import CommunicationRetrievalError
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.result import TestResult
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.comms import mock_comms_entity_gets

PATCH_RESOURCES = "medperf.comms.entity_resources.resources.{}"


# Setup Benchmark
def setup_benchmark_fs(ents, fs):
    bmks_path = storage_path(config.benchmarks_storage)
    for ent in ents:
        if not isinstance(ent, dict):
            # Assume we're passing ids
            ent = {"id": str(ent)}
        id = ent["id"]
        bmk_filepath = os.path.join(bmks_path, str(id), config.benchmarks_filename)
        bmk_contents = TestBenchmark(**ent)
        cubes_ids = bmk_contents.models
        cubes_ids.append(bmk_contents.data_preparation_mlcube)
        cubes_ids.append(bmk_contents.reference_model_mlcube)
        cubes_ids.append(bmk_contents.data_evaluator_mlcube)
        cubes_ids = list(set(cubes_ids))
        setup_cube_fs(cubes_ids, fs)
        try:
            fs.create_file(bmk_filepath, contents=yaml.dump(bmk_contents.dict()))
        except FileExistsError:
            pass


def setup_benchmark_comms(mocker, comms, all_ents, user_ents, uploaded):
    generate_fn = TestBenchmark
    comms_calls = {
        "get_all": "get_benchmarks",
        "get_user": "get_user_benchmarks",
        "get_instance": "get_benchmark",
        "upload_instance": "upload_benchmark",
    }
    mocker.patch.object(comms, "get_benchmark_models", return_value=[])
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ents, user_ents, uploaded
    )


# Setup Cube
def setup_cube_fs(ents, fs):
    cubes_path = storage_path(config.cubes_storage)
    for ent in ents:
        if not isinstance(ent, dict):
            # Assume we're passing ids
            ent = {"id": str(ent)}
        id = ent["id"]
        meta_cube_file = os.path.join(
            cubes_path, str(id), config.cube_metadata_filename
        )
        cube = TestCube(**ent)
        meta = cube.dict()
        try:
            fs.create_file(meta_cube_file, contents=yaml.dump(meta))
        except FileExistsError:
            pass


def setup_cube_comms(mocker, comms, all_ents, user_ents, uploaded):
    generate_fn = TestCube
    comms_calls = {
        "get_all": "get_cubes",
        "get_user": "get_user_cubes",
        "get_instance": "get_cube_metadata",
        "upload_instance": "upload_mlcube",
    }
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ents, user_ents, uploaded
    )


def generate_cubefile_fn(fs, path, filename):
    # all_ids = [ent["id"] if type(ent) == dict else ent for ent in all_ents]

    def cubefile_fn(url, cube_path, *args):
        if url == "broken_url":
            raise CommunicationRetrievalError
        filepath = os.path.join(cube_path, path, filename)
        try:
            fs.create_file(filepath)
        except FileExistsError:
            pass
        hash = get_file_hash(filepath)
        # special case: tarball file
        if filename == config.tarball_filename:
            return hash
        return filepath, hash

    return cubefile_fn


def setup_cube_comms_downloads(mocker, fs):
    cube_path = ""
    cube_file = config.cube_filename
    params_path = config.workspace_path
    params_file = config.params_filename
    add_path = config.additional_path
    add_file = config.tarball_filename
    img_path = config.image_path
    img_file = "img.tar.gz"

    get_cube_fn = generate_cubefile_fn(fs, cube_path, cube_file)
    get_params_fn = generate_cubefile_fn(fs, params_path, params_file)
    get_add_fn = generate_cubefile_fn(fs, add_path, add_file)
    get_img_fn = generate_cubefile_fn(fs, img_path, img_file)

    mocker.patch(PATCH_RESOURCES.format("get_cube"), side_effect=get_cube_fn)
    mocker.patch(PATCH_RESOURCES.format("get_cube_params"), side_effect=get_params_fn)
    mocker.patch(PATCH_RESOURCES.format("get_cube_additional"), side_effect=get_add_fn)
    mocker.patch(PATCH_RESOURCES.format("get_cube_image"), side_effect=get_img_fn)


# Setup Dataset
def setup_dset_fs(ents, fs):
    dsets_path = storage_path(config.data_storage)
    for ent in ents:
        if not isinstance(ent, dict):
            # Assume passing ids
            ent = {"id": str(ent)}
        id = ent["id"]
        reg_dset_file = os.path.join(dsets_path, str(id), config.reg_file)
        dset_contents = TestDataset(**ent)
        cube_id = dset_contents.data_preparation_mlcube
        setup_cube_fs([cube_id], fs)
        try:
            fs.create_file(reg_dset_file, contents=yaml.dump(dset_contents.dict()))
        except FileExistsError:
            pass


def setup_dset_comms(mocker, comms, all_ents, user_ents, uploaded):
    generate_fn = TestDataset
    comms_calls = {
        "get_all": "get_datasets",
        "get_user": "get_user_datasets",
        "get_instance": "get_dataset",
        "upload_instance": "upload_dataset",
    }
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ents, user_ents, uploaded
    )


# Setup Result
def setup_result_fs(ents, fs):
    results_path = storage_path(config.results_storage)
    for ent in ents:
        if not isinstance(ent, dict):
            # Assume passing ids
            ent = {"id": str(ent)}
        id = ent["id"]
        result_file = os.path.join(results_path, str(id), config.results_info_file)
        bmk_id = ent.get("benchmark", 1)
        cube_id = ent.get("model", 1)
        dataset_id = ent.get("dataset", 1)
        setup_benchmark_fs([bmk_id], fs)
        setup_cube_fs([cube_id], fs)
        setup_dset_fs([dataset_id], fs)
        result_contents = TestResult(**ent)
        try:
            fs.create_file(result_file, contents=yaml.dump(result_contents.dict()))
        except FileExistsError:
            pass


def setup_result_comms(mocker, comms, all_ents, user_ents, uploaded):
    generate_fn = TestResult
    comms_calls = {
        "get_all": "get_results",
        "get_user": "get_user_results",
        "get_instance": "get_result",
        "upload_instance": "upload_result",
    }

    # Enable dset retrieval since its required for result creation
    setup_dset_comms(mocker, comms, [1], [1], uploaded)
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ents, user_ents, uploaded
    )
