import os
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
    for ent in ents:
        # Assume we're passing ids, local_ids, or dicts
        if isinstance(ent, dict):
            bmk_contents = TestBenchmark(**ent)
        elif isinstance(ent, int) or isinstance(ent, str) and ent.isdigit():
            bmk_contents = TestBenchmark(id=str(ent))
        else:
            bmk_contents = TestBenchmark(id=None, name=ent)

        bmk_filepath = os.path.join(bmk_contents.path, config.benchmarks_filename)
        cubes_ids = []
        cubes_ids.append(bmk_contents.data_preparation_mlcube)
        cubes_ids.append(bmk_contents.reference_model_mlcube)
        cubes_ids.append(bmk_contents.data_evaluator_mlcube)
        cubes_ids = list(set(cubes_ids))
        setup_cube_fs(cubes_ids, fs)
        try:
            fs.create_file(bmk_filepath, contents=yaml.dump(bmk_contents.todict()))
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
    mocker.patch.object(comms, "get_benchmark_model_associations", return_value=[])
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ents, user_ents, uploaded
    )


# Setup Cube
def setup_cube_fs(ents, fs):
    for ent in ents:
        # Assume we're passing ids, names, or dicts
        if isinstance(ent, dict):
            cube = TestCube(**ent)
        elif isinstance(ent, int) or isinstance(ent, str) and ent.isdigit():
            cube = TestCube(id=str(ent))
        else:
            cube = TestCube(id=None, name=ent)

        meta_cube_file = os.path.join(cube.path, config.cube_metadata_filename)
        meta = cube.todict()
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
    stages_path = ""
    stages_file = config.stages_filename

    get_cube_fn = generate_cubefile_fn(fs, cube_path, cube_file)
    get_params_fn = generate_cubefile_fn(fs, params_path, params_file)
    get_add_fn = generate_cubefile_fn(fs, add_path, add_file)
    get_img_fn = generate_cubefile_fn(fs, img_path, img_file)
    get_stages_fn = generate_cubefile_fn(fs, stages_path, stages_file)


    mocker.patch(PATCH_RESOURCES.format("get_cube"), side_effect=get_cube_fn)
    mocker.patch(PATCH_RESOURCES.format("get_cube_params"), side_effect=get_params_fn)
    mocker.patch(PATCH_RESOURCES.format("get_cube_additional"), side_effect=get_add_fn)
    mocker.patch(PATCH_RESOURCES.format("get_cube_image"), side_effect=get_img_fn)
    mocker.patch(PATCH_RESOURCES.format("get_cube_stages"), side_effect=get_stages_fn)


# Setup Dataset
def setup_dset_fs(ents, fs):
    for ent in ents:
        # Assume we're passing ids, generated_uids, or dicts
        if isinstance(ent, dict):
            dset_contents = TestDataset(**ent)
        elif isinstance(ent, int) or isinstance(ent, str) and ent.isdigit():
            dset_contents = TestDataset(id=str(ent))
        else:
            dset_contents = TestDataset(id=None, generated_uid=ent)

        reg_dset_file = os.path.join(dset_contents.path, config.reg_file)
        cube_id = dset_contents.data_preparation_mlcube
        setup_cube_fs([cube_id], fs)
        try:
            fs.create_file(reg_dset_file, contents=yaml.dump(dset_contents.todict()))
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
    for ent in ents:
        # Assume we're passing ids, names, or dicts
        if isinstance(ent, dict):
            result_contents = TestResult(**ent)
        elif isinstance(ent, int) or isinstance(ent, str) and ent.isdigit():
            result_contents = TestResult(id=str(ent))
        else:
            result_contents = TestResult(id=None, name=ent)

        result_file = os.path.join(result_contents.path, config.results_info_file)
        bmk_id = result_contents.benchmark
        cube_id = result_contents.model
        dataset_id = result_contents.dataset
        setup_benchmark_fs([bmk_id], fs)
        setup_cube_fs([cube_id], fs)
        setup_dset_fs([dataset_id], fs)

        try:
            fs.create_file(result_file, contents=yaml.dump(result_contents.todict()))
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
