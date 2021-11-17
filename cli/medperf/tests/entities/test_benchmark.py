from medperf.entities import Benchmark, Server
from medperf.tests.mocks.requests import benchmark_body
from medperf.tests.utils import rand_l
import medperf

import pytest

PATCH_SERVER = "medperf.entities.benchmark.Server.{}"


@pytest.fixture()
def server(mocker):
    server = Server("mock.url")
    mocker.patch(PATCH_SERVER.format("get_benchmark"), side_effect=benchmark_body)
    mocker.patch(PATCH_SERVER.format("get_benchmark_models"), return_value=[])
    return server


def test_get_benchmark_retrieves_benchmark_from_server(mocker, server):
    # Arrange
    spy = mocker.spy(medperf.entities.benchmark.Server, "get_benchmark")

    # Act
    uid = 1
    Benchmark.get(uid, server)

    # Assert
    spy.assert_called_once_with(uid)


@pytest.mark.parametrize("uid", rand_l(1, 5000, 10))
def test_get_benchmark_retrieves_models_from_server(mocker, server, uid):
    # Arrange
    spy = mocker.spy(medperf.entities.benchmark.Server, "get_benchmark_models")

    # Act
    Benchmark.get(uid, server)

    # Assert
    spy.assert_called_once_with(uid)


def test_benchmark_includes_reference_model_in_models(server):
    # Act
    uid = 1
    benchmark = Benchmark.get(uid, server)

    # Assert
    assert benchmark.reference_model in benchmark.models


@pytest.mark.parametrize("models", [rand_l(1, 5000, 4) for _ in range(5)])
def test_benchmark_includes_additional_models_in_modles(mocker, server, models):
    # Arrange
    mocker.patch(PATCH_SERVER.format("get_benchmark_models"), return_value=models)

    # Act
    uid = 1
    benchmark = Benchmark.get(uid, server)

    # Assert
    assert set(models).issubset(set(benchmark.models))
