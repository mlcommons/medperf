import os
import pytest
from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.result import Result
from medperf.utils import storage_path
from medperf import config


@pytest.fixture(params=[Benchmark, Cube, Dataset, Result])
def Implementation(request):
    return request.param


@pytest.fixture()
def setup(Implementation, fs):
    if Implementation == Benchmark:
        setup_benchmark_fs([1, 2, 3], fs)
    elif Implementation == Cube:
        setup_cube_fs([1, 2, 3], fs)
    elif Implementation == Dataset:
        setup_dset_fs([1, 2, 3], fs)
    elif Implementation == Result:
        setup_result_fs([1, 2, 3], fs)


def setup_benchmark_fs(ids, fs):
    bmks_path = storage_path(config.benchmarks_storage)
    for id in ids:
        id = str(id)
        bmk_filepath = os.path.join(bmks_path, id, config.benchmarks_filename)
        fs.create_file(bmk_filepath)


def setup_cube_fs(ids, fs):
    cubes_path = storage_path(config.cubes_storage)
    for id in ids:
        id = str(id)
        meta_cube_file = os.path.join(cubes_path, id, config.cube_metadata_filename)
        hash_cube_file = os.path.join(cubes_path, id, config.cube_hashes_filename)
        fs.create_file(meta_cube_file)
        fs.create_file(hash_cube_file)


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


def test_all_returns_list_of_entity_instances(Implementation, setup, fs):
    # Arrange

    # Act
    # TODO: Get the entity we want to test and call the function
    # TODO: Entity is a parameter, and the input/output are passed as parameters as well
    entities = Implementation.all()

    # Assert
    # Ensure the output of the call is the expected one
    assert len(entities) == 3

