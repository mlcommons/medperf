from medperf.entities import Benchmark
from medperf.comms import Comms
from medperf.tests.mocks.requests import benchmark_body
from medperf.tests.utils import rand_l

import pytest


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    mocker.patch.object(comms, "get_benchmark", side_effect=benchmark_body)
    mocker.patch.object(comms, "get_benchmark_models", return_value=[])
    return comms


def test_get_benchmark_retrieves_benchmark_from_comms(mocker, comms):
    # Arrange
    spy = mocker.spy(comms, "get_benchmark")

    # Act
    uid = 1
    print(Benchmark.get(uid, comms))

    # Assert
    spy.assert_called_once_with(uid)


@pytest.mark.parametrize("uid", rand_l(1, 5000, 10))
def test_get_benchmark_retrieves_models_from_comms(mocker, comms, uid):
    # Arrange
    spy = mocker.spy(comms, "get_benchmark_models")

    # Act
    Benchmark.get(uid, comms)

    # Assert
    spy.assert_called_once_with(uid)


def test_benchmark_includes_reference_model_in_models(comms):
    # Act
    uid = 1
    benchmark = Benchmark.get(uid, comms)

    # Assert
    assert benchmark.reference_model in benchmark.models


@pytest.mark.parametrize("models", [rand_l(1, 5000, 4) for _ in range(5)])
def test_benchmark_includes_additional_models_in_modles(mocker, comms, models):
    # Arrange
    mocker.patch.object(comms, "get_benchmark_models", return_value=models)

    # Act
    uid = 1
    benchmark = Benchmark.get(uid, comms)

    # Assert
    assert set(models).issubset(set(benchmark.models))
