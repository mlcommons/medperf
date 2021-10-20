from medperf.entities import Benchmark, Server
from medperf.tests.mocks.requests import benchmark_body
import medperf

import pytest


@pytest.fixture()
def server(mocker):
    server = Server("mock.url")
    patch_server = "medperf.entities.benchmark.Server.{}"
    mocker.patch(patch_server.format("get_benchmark"), side_effect=benchmark_body)
    mocker.patch(patch_server.format("get_benchmark_models"), return_value=[5, 6, 7])
    return server


def test_get_benchmark_retrieves_benchmark_from_server(mocker, server):
    # Arrange
    spy = mocker.spy(medperf.entities.benchmark.Server, "get_benchmark")

    # Act
    uid = 1
    Benchmark.get(uid, server)

    # Assert
    spy.assert_called_once_with(uid)


def test_get_benchmark_retrieves_models_from_server(mocker, server):
    # Arrange
    spy = mocker.spy(medperf.entities.benchmark.Server, "get_benchmark_models")

    # Act
    uid = 1
    Benchmark.get(uid, server)

    # Assert
    spy.assert_called_once_with(uid)


def test_benchmark_includes_reference_model_in_models(server):
    # Act
    uid = 1
    benchmark = Benchmark.get(uid, server)

    # Assert
    assert benchmark.reference_model in benchmark.models


def test_benchmark_includes_additional_models_in_modles(server):
    # Act
    uid = 1
    benchmark = Benchmark.get(uid, server)

    # Assert
    assert set([5, 6, 7]).issubset(set(benchmark.models))
