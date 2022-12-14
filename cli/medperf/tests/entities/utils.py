import os
from medperf.utils import storage_path
from medperf import config
import yaml

from medperf.enums import Status
from medperf.exceptions import CommunicationRetrievalError


def get_comms_instance_behavior(generate_fn, ids):
    def get_behavior(id):
        if id in ids:
            id = str(id)
            return generate_fn(id=id)
        else:
            raise CommunicationRetrievalError

    return get_behavior


def upload_comms_instance_behavior(uploaded):
    def upload_behavior(entity_dict):
        uploaded.append(entity_dict)
        return entity_dict

    return upload_behavior


def mock_comms_entity_gets(
    mocker, comms, generate_fn, comms_calls, all_ids, user_ids, uploaded
):
    get_all = comms_calls["get_all"]
    get_user = comms_calls["get_user"]
    get_instance = comms_calls["get_instance"]
    upload_instance = comms_calls["upload_instance"]

    instances = [generate_fn(id=id) for id in all_ids]
    user_instances = [generate_fn(id=id) for id in user_ids]
    mocker.patch.object(comms, get_all, return_value=instances)
    mocker.patch.object(comms, get_user, return_value=user_instances)
    get_behavior = get_comms_instance_behavior(generate_fn, all_ids)
    mocker.patch.object(
        comms, get_instance, side_effect=get_behavior,
    )
    upload_behavior = upload_comms_instance_behavior(uploaded)
    mocker.patch.object(comms, upload_instance, side_effect=upload_behavior)


# BENCHMARK MOCKING
def generate_benchmark(**kwargs):
    return {
        "id": kwargs.get("id", 1),
        "name": kwargs.get("name", "name"),
        "description": kwargs.get("description", "description"),
        "docs_url": kwargs.get("docs_url", ""),
        "created_at": kwargs.get("created_at", "created_at"),
        "modified_at": kwargs.get("modified_at", "modified_at"),
        "approved_at": kwargs.get("approved_at", "approved_at"),
        "owner": kwargs.get("owner", 1),
        "demo_dataset_tarball_url": kwargs.get(
            "demo_dataset_tarball_url", "demo_dataset_tarball_url"
        ),
        "demo_dataset_tarball_hash": kwargs.get(
            "demo_dataset_tarball_hash", "demo_dataset_tarball_hash"
        ),
        "demo_dataset_generated_uid": kwargs.get(
            "demo_dataset_generated_uid", "demo_dataset_generated_uid"
        ),
        "data_preparation_mlcube": kwargs.get("data_preparation_mlcube", 1),
        "reference_model_mlcube": kwargs.get("reference_model_mlcube", 2),
        "models": kwargs.get("models", [2]),
        "data_evaluator_mlcube": kwargs.get("data_evaluator_mlcube", 3),
        "state": kwargs.get("state", "PRODUCTION"),
        "is_valid": kwargs.get("is_valid", True),
        "is_active": kwargs.get("is_active", True),
        "approval_status": kwargs.get("approval_status", Status.APPROVED.value),
        "metadata": kwargs.get("metadata", {}),
        "user_metadata": kwargs.get("user_metadata", {}),
    }


def setup_benchmark_fs(ids, fs):
    bmks_path = storage_path(config.benchmarks_storage)
    for id in ids:
        id = str(id)
        bmk_filepath = os.path.join(bmks_path, id, config.benchmarks_filename)
        bmk_contents = generate_benchmark(id=id)
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


def setup_benchmark_comms(mocker, comms, all_ids, user_ids, uploaded):
    generate_fn = generate_benchmark
    comms_calls = {
        "get_all": "get_benchmarks",
        "get_user": "get_user_benchmarks",
        "get_instance": "get_benchmark",
        "upload_instance": "upload_benchmark",
    }
    mocker.patch.object(comms, "get_benchmark_models", return_value=[])
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ids, user_ids, uploaded
    )


# MLCUBE MOCKING
def generate_cube(**kwargs):
    return {
        "id": kwargs.get("id", 1),
        "name": kwargs.get("name", "name"),
        "git_mlcube_url": kwargs.get("git_mlcube_url", "git_mlcube_url"),
        "mlcube_hash": kwargs.get("mlcube_hash", "mlcube_hash"),
        "git_parameters_url": kwargs.get("git_parameters_url", "git_parameters_url"),
        "parameters_hash": kwargs.get("parameters_hash", "parameters_hash"),
        "image_tarball_url": kwargs.get("image_tarball_url", "image_tarball_url"),
        "image_tarball_hash": kwargs.get("image_tarball_hash", "image_tarball_hash"),
        "additional_files_tarball_url": kwargs.get(
            "additional_files_tarball_url", "additional_files_tarball_url"
        ),
        "additional_files_tarball_hash": kwargs.get(
            "additional_files_tarball_hash", "additional_files_tarball_hash"
        ),
        "state": kwargs.get("state", "PRODUCTION"),
        "is_valid": kwargs.get("is_valid", True),
        "owner": kwargs.get("owner", 1),
        "metadata": kwargs.get("metadata", {}),
        "user_metadata": kwargs.get("user_metadata", {}),
        "created_at": kwargs.get("created_at", "created_at"),
        "modified_at": kwargs.get("modified_at", "modified_at"),
    }


def generate_cube_hashes(**kwargs):
    return {
        "additional_files_tarball_hash": kwargs.get(
            "additional_files_tarball_hash", "additional_files_tarball_hash"
        ),
        "image_tarball_hash": kwargs.get("image_tarball_hash", "image_tarball_hash"),
    }


def setup_cube_fs(ids, fs):
    cubes_path = storage_path(config.cubes_storage)
    for id in ids:
        id = str(id)
        meta_cube_file = os.path.join(cubes_path, id, config.cube_metadata_filename)
        hash_cube_file = os.path.join(cubes_path, id, config.cube_hashes_filename)
        meta = generate_cube(id=id)
        hashes = generate_cube_hashes(id=id)
        try:
            fs.create_file(meta_cube_file, contents=yaml.dump(meta))
            fs.create_file(hash_cube_file, contents=yaml.dump(hashes))
        except FileExistsError:
            pass


def setup_cube_comms(mocker, comms, all_ids, user_ids, uploaded):
    generate_fn = generate_cube
    comms_calls = {
        "get_all": "get_cubes",
        "get_user": "get_user_cubes",
        "get_instance": "get_cube_metadata",
        "upload_instance": "upload_mlcube",
    }
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ids, user_ids, uploaded
    )


# DATASET MOCKING
def generate_dset(**kwargs):
    return {
        "id": kwargs.get("id", 1),
        "name": kwargs.get("name", "name"),
        "description": kwargs.get("description", "description"),
        "location": kwargs.get("location", "location"),
        "data_preparation_mlcube": kwargs.get("data_preparation_mlcube", 1),
        "input_data_hash": kwargs.get("input_data_hash", "input_data_hash"),
        "generated_uid": kwargs.get("generated_uid", "generated_uid"),
        "split_seed": kwargs.get("split_seed", "split_seed"),
        "generated_metadata": kwargs.get("generated_metadata", "generated_metadata"),
        "status": kwargs.get("status", Status.APPROVED.value),  # not in the server
        "state": kwargs.get("state", "PRODUCTION"),
        "separate_labels": kwargs.get("separate_labels", False),  # not in the server
        "is_valid": kwargs.get("is_valid", True),
        "user_metadata": kwargs.get("user_metadata", {}),
        "created_at": kwargs.get("created_at", "created_at"),
        "modified_at": kwargs.get("modified_at", "modified_at"),
        "owner": kwargs.get("owner", 1),
    }


def setup_dset_fs(ids, fs):
    dsets_path = storage_path(config.data_storage)
    for id in ids:
        id = str(id)
        reg_dset_file = os.path.join(dsets_path, id, config.reg_file)
        dset_contents = generate_dset(id=id)
        cube_id = dset_contents["data_preparation_mlcube"]
        setup_cube_fs([cube_id], fs)
        try:
            fs.create_file(reg_dset_file, contents=yaml.dump(dset_contents))
        except FileExistsError:
            pass


def setup_dset_comms(mocker, comms, all_ids, user_ids, uploaded):
    generate_fn = generate_dset
    comms_calls = {
        "get_all": "get_datasets",
        "get_user": "get_user_datasets",
        "get_instance": "get_dataset",
        "upload_instance": "upload_dataset",
    }
    mock_comms_entity_gets(
        mocker, comms, generate_fn, comms_calls, all_ids, user_ids, uploaded
    )


# RESULT MOCKING
def generate_result(**kwargs):
    return {
        "id": kwargs.get("id", 1),
        "name": kwargs.get("name", "name"),
        "owner": kwargs.get("owner", 1),
        "benchmark": kwargs.get("benchmark", 1),
        "model": kwargs.get("model", 1),
        "dataset": kwargs.get("dataset", 1),
        "results": kwargs.get("results", {}),
        "metadata": kwargs.get("metadata", {}),
        "approval_status": kwargs.get("approval_status", Status.APPROVED.value),
        "approved_at": kwargs.get("approved_at", "approved_at"),
        "created_at": kwargs.get("created_at", "created_at"),
        "modified_at": kwargs.get("modified_at", "modified_at"),
    }


def setup_result_fs(ids, fs):
    results_path = storage_path(config.results_storage)
    for id in ids:
        id = str(id)
        result_file = os.path.join(results_path, id, config.results_info_file)
        result_contents = generate_result(id=id)
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


def setup_result_comms(mocker, comms, all_ids, user_ids, uploaded):
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
        mocker, comms, generate_fn, comms_calls, all_ids, user_ids, uploaded
    )

