import pytest
from medperf.entities.benchmark import Benchmark
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.result import Result
from medperf.tests.entities.utils import *


@pytest.fixture(params=[Benchmark, Cube, Dataset, Result])
def Implementation(request):
    return request.param


@pytest.fixture(params={"local": [1, 2, 3], "remote": [4, 5, 6], "user": []})
def setup(request, mocker, comms, Implementation, fs):
    local_ids = request.param["local"]
    remote_ids = request.param["remote"]
    user_ids = request.param["user"]

    if Implementation == Benchmark:
        setup_fs = setup_benchmark_fs
        setup_comms = setup_benchmark_comms
    elif Implementation == Cube:
        setup_fs = setup_cube_fs
        setup_comms = setup_cube_comms
    elif Implementation == Dataset:
        setup_fs = setup_dset_fs
        setup_comms = setup_result_comms
    elif Implementation == Result:
        setup_fs = setup_result_fs
        setup_comms = setup_result_comms

    setup_fs(local_ids, fs)
    setup_comms(mocker, comms, remote_ids, user_ids)

    return request.param


@pytest.mark.parametrize(
    "setup",
    [{"local": [283, 17, 493], "remote": [283, 1, 2], "user": []}],
    indirect=True,
)
def test_all_returns_all_remote_and_local(Implementation, setup, fs):
    # Arrange
    ids = setup
    local_ids = set(ids["local"])
    remote_ids = set(ids["remote"])
    all_ids = local_ids.union(remote_ids)

    # Act
    entities = Implementation.all()

    # Assert
    retrieved_ids = set([int(e.todict()["id"]) for e in entities])
    assert type(entities[0]) == Implementation
    assert all_ids == retrieved_ids

