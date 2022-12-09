import pytest
from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.result import Result
from .utils import *


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


def test_all_returns_list_of_entity_instances(Implementation, setup, fs):
    # Arrange

    # Act
    # TODO: Get the entity we want to test and call the function
    # TODO: Entity is a parameter, and the input/output are passed as parameters as well
    entities = Implementation.all()

    # Assert
    # Ensure the output of the call is the expected one
    assert len(entities) == 3

