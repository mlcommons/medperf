import os
from medperf.utils import storage_path
from medperf import config
import yaml

from medperf.exceptions import CommunicationRetrievalError
from medperf.tests.mocks.benchmark import generate_benchmark
from medperf.tests.mocks.dataset import generate_dset
from medperf.tests.mocks.result import generate_result
from medperf.tests.mocks.cube import generate_cube
from medperf.tests.mocks.comms import mock_comms_entity_gets


# Setup Benchmark
def setup_benchmark_fs(ents, fs):
    bmks_path = storage_path(config.benchmarks_storage)
    for ent in ents:
        if type(ent) != dict:
            # Assume we're passing ids
            ent = {"id": str(ent)}
        id = ent["id"]
        bmk_filepath = os.path.join(bmks_path, id, config.benchmarks_filename)
        bmk_contents = generate_benchmark(**ent)
        cubes_ids = bmk_contents["models"]
        cubes_ids.append(bmk_contents["data_preparation_mlcube"])
        cubes_ids.append(bmk_contents["reference_model_mlcube"])
        cubes_ids.append(bmk_contents["data_evaluator_mlcube"])
        cubes_ids = list(set(cubes_ids))
        setup_cube_fs(cubes_ids, fs)
        try:
            fs.create_file(bmk_filepath, contents=yaml.dump(bmk_contents))
        except FileExistsError:
            pass


def setup_benchmark_comms(mocker, comms, all_ents, user_ents, uploaded):
    generate_fn = generate_benchmark
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
def generate_cube_hashes(**kwargs):
    return {
        "additional_files_tarball_hash": kwargs.get(
            "additional_files_tarball_hash", "additional_files_tarball_hash"
        ),
        "image_tarball_hash": kwargs.get("image_tarball_hash", "image_tarball_hash"),
    }


def setup_cube_fs(ents, fs):
    cubes_path = storage_path(config.cubes_storage)
    for ent in ents:
        if type(ent) != dict:
            # Assume we're passing ids
            ent = {"id": str(ent)}
        id = ent["id"]
        meta_cube_file = os.path.join(cubes_path, id, config.cube_metadata_filename)
        hash_cube_file = os.path.join(cubes_path, id, config.cube_hashes_filename)
        meta = generate_cube(id=id)
        hashes = generate_cube_hashes(**ent)
        try:
            fs.create_file(meta_cube_file, contents=yaml.dump(meta))
            fs.create_file(hash_cube_file, contents=yaml.dump(hashes))
        except FileExistsError:
            pass


def setup_cube_comms(mocker, comms, all_ents, user_ents, uploaded):
    generate_fn = generate_cube
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

    def cubefile_fn(url, cube_path):
        if url == "broken_url":
            raise CommunicationRetrievalError
        filepath = os.path.join(cube_path, path, filename)
        try:
            fs.create_file(filepath)
        except FileExistsError:
            pass
        return filepath

    return cubefile_fn


def setup_cube_comms_downloads(mocker, comms, fs):
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

    mocker.patch.object(comms, "get_cube", side_effect=get_cube_fn)
    mocker.patch.object(comms, "get_cube_params", side_effect=get_params_fn)
    mocker.patch.object(comms, "get_cube_additional", side_effect=get_add_fn)
    mocker.patch.object(comms, "get_cube_image", side_effect=get_img_fn)


# Setup Dataset
def setup_dset_fs(ents, fs):
    dsets_path = storage_path(config.data_storage)
    for ent in ents:
        if type(ent) != dict:
            # Assume passing ids
            ent = {"id": str(ent)}
        id = ent["id"]
        reg_dset_file = os.path.join(dsets_path, id, config.reg_file)
        dset_contents = generate_dset(**ent)
        cube_id = dset_contents["data_preparation_mlcube"]
        setup_cube_fs([cube_id], fs)
        try:
            fs.create_file(reg_dset_file, contents=yaml.dump(dset_contents))
        except FileExistsError:
            pass


def setup_dset_comms(mocker, comms, all_ents, user_ents, uploaded):
    generate_fn = generate_dset
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
        if type(ent) != dict:
            # Assume passing ids
            ent = {"id": str(ent)}
        id = ent["id"]
        result_file = os.path.join(results_path, id, config.results_info_file)
        result_contents = generate_result(**ent)
        bmk_id = result_contents["benchmark"]
        cube_id = result_contents["model"]
        dataset_id = result_contents["dataset"]
        setup_benchmark_fs([bmk_id], fs)
        setup_cube_fs([cube_id], fs)
        setup_dset_fs([dataset_id], fs)
        try:
            fs.create_file(result_file, contents=yaml.dump(result_contents))
        except FileExistsError:
            pass


def setup_result_comms(mocker, comms, all_ents, user_ents, uploaded):
    generate_fn = generate_result
    def_result = generate_result()
    comms_calls = {
        "get_all": "get_results",
        "get_user": "get_user_results",
        "get_instance": "get_result",
        "upload_instance": "upload_result",
    }

    # Enable dset retrieval since its required for result creation
    setup_dset_comms(
        mocker, comms, [def_result["dataset"]], [def_result["dataset"]], uploaded
    )
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ents, user_ents, uploaded
    )
