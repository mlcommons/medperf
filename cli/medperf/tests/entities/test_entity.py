import pytest
from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.result import Result
from medperf.tests.entities.utils import *


@pytest.fixture(params=[Benchmark, Cube, Dataset, Result])
def Implementation(request):
    return request.param


@pytest.fixture(params=[1, 2, 3])
def setup(request, Implementation, fs):
    ids = request.param
    if Implementation == Benchmark:
        setup_benchmark_fs(ids, fs)
    elif Implementation == Cube:
        setup_cube_fs(ids, fs)
    elif Implementation == Dataset:
        setup_dset_fs(ids, fs)
    elif Implementation == Result:
        setup_result_fs(ids, fs)
    return ids


@pytest.mark.parametrize("setup", [[283, 17, 493]], indirect=True)
def test_all_returns_list_of_entity_instances(Implementation, setup, fs):
    # Arrange
    ids = setup

    # Act
    entities = Implementation.all()

    # Assert
    retrieved_ids = [int(e.todict()["id"]) for e in entities]
    assert type(entities[0]) == Implementation
    assert ids == retrieved_ids

