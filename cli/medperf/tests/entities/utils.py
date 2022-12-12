import os
from medperf.utils import storage_path
from medperf import config
import yaml

from medperf.enums import Status


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
        "reference_model_mlcube": kwargs.get("data_preparation_mlcube", 2),
        "models": kwargs.get("models", [2]),
        "data_evaluator_mlcube": kwargs.get("data_evaluator_mlcube", 3),
        "state": kwargs.get("state", "PRODUCTION"),
        "is_valid": kwargs.get("is_valid", True),
        "is_active": kwargs.get("is_active", True),
        "approval_status": kwargs.get("approval_status", Status.PENDING.value),
        "metadata": kwargs.get("metadata", {}),
        "user_metadata": kwargs.get("user_metadata", {}),
    }


def setup_benchmark_fs(ids, fs):
    bmks_path = storage_path(config.benchmarks_storage)
    for id in ids:
        id = str(id)
        bmk_filepath = os.path.join(bmks_path, id, config.benchmarks_filename)
        bmk_contents = generate_benchmark(id=id)
        fs.create_file(bmk_filepath, contents=yaml.dump(bmk_contents))


# MLCUBE MOCKING
def generate_cube(**kwargs):
    return (
        {
            "id": kwargs.get("id", 1),
            "name": kwargs.get("name", "name"),
            "git_mlcube_url": kwargs.get("git_mlcube_url", "git_mlcube_url"),
            "git_parameters_url": kwargs.get(
                "git_parameters_url", "git_parameters_url"
            ),
            "image_tarball_url": kwargs.get("image_tarball_url", "image_tarball_url"),
            "image_tarball_hash": kwargs.get(
                "image_tarball_hash", "image_tarball_hash"
            ),
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
        },
        {
            "additional_files_tarball_hash": kwargs.get(
                "additional_files_tarball_hash", "additional_files_tarball_hash"
            ),
            "image_tarball_hash": kwargs.get(
                "image_tarball_hash", "image_tarball_hash"
            ),
        },
    )


def setup_cube_fs(ids, fs):
    cubes_path = storage_path(config.cubes_storage)
    for id in ids:
        id = str(id)
        meta_cube_file = os.path.join(cubes_path, id, config.cube_metadata_filename)
        hash_cube_file = os.path.join(cubes_path, id, config.cube_hashes_filename)
        meta, hashes = generate_cube(id=id)
        fs.create_file(meta_cube_file, contents=yaml.dump(meta))
        fs.create_file(hash_cube_file, contents=yaml.dump(hashes))


def setup_dset_fs(ids, fs):
    dsets_path = storage_path(config.data_storage)
    for id in ids:
        id = str(id)
        reg_dset_file = os.path.join(dsets_path, id, config.reg_file)
        fs.create_file(reg_dset_file)


def setup_result_fs(ids, fs):
    results_path = storage_path(config.results_storage)
    for id in ids:
        id = str(id)
        result_file = os.path.join(results_path, id, config.results_info_file)
        fs.create_file(result_file)

