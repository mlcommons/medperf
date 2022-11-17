import os
import pytest
from unittest.mock import mock_open, ANY

import medperf.config as config
from medperf.comms.interface import Comms
from medperf.utils import storage_path
from medperf.entities.benchmark import Benchmark
from medperf.tests.mocks.requests import benchmark_body, benchmark_dict
from medperf.exceptions import CommunicationRetrievalError


PATCH_BENCHMARK = "medperf.entities.benchmark.{}"


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    mocker.patch.object(comms, "get_benchmark", side_effect=benchmark_body)
    mocker.patch.object(comms, "get_benchmark_models", return_value=[])
    config.comms = comms
    return comms


@pytest.fixture
def no_local(mocker):
    mocker.patch("os.listdir", return_value=[])
    mocker.patch(PATCH_BENCHMARK.format("Benchmark.write"))


def test_all_calls_comms(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "get_benchmarks", return_value=[])

    # Act
    Benchmark.all()

    # Assert
    spy.assert_called_once()


def test_all_looks_at_correct_path_if_comms_failed(mocker, comms):
    # Arrange
    bmks_path = storage_path(config.benchmarks_storage)
    fs = iter([(".", (), ())])
    spy = mocker.patch("os.walk", return_value=fs)
    mocker.patch.object(
        comms, "get_benchmarks", side_effect=CommunicationRetrievalError
    )

    # Act
    Benchmark.all()

    # Assert
    spy.assert_called_once_with(bmks_path)


def test_all_doesnt_call_comms_if_only_local(mocker, comms):
    # Arrange
    fs = iter([(".", (), ())])
    mocker.patch("os.walk", return_value=fs)
    spy = mocker.patch.object(
        comms, "get_benchmarks", side_effect=CommunicationRetrievalError
    )

    # Act
    Benchmark.all(local_only=True)

    # Assert
    spy.assert_not_called()


def test_get_benchmark_retrieves_benchmark_from_comms(mocker, no_local, comms):
    # Arrange
    spy = mocker.spy(comms, "get_benchmark")

    # Act
    uid = 1
    Benchmark.get(uid)

    # Assert
    spy.assert_called_once_with(uid)


@pytest.mark.parametrize("uid", [4, 82, 77, 38])
def test_get_benchmark_retrieves_models_from_comms(mocker, no_local, comms, uid):
    # Arrange
    spy = mocker.spy(comms, "get_benchmark_models")

    # Act
    Benchmark.get(uid)

    # Assert
    spy.assert_called_once_with(uid)


@pytest.mark.parametrize("benchmarks_uids", [[1, 8, 33]])
def test_get_benchmark_retrieves_local_benchmarks(mocker, comms, benchmarks_uids):
    # Arrange
    benchmarks_uids = [str(uid) for uid in benchmarks_uids]
    mocker.patch("os.listdir", return_value=benchmarks_uids)
    mocker.patch(PATCH_BENCHMARK.format("Benchmark.write"))
    mocker.patch.object(comms, "get_benchmark", side_effect=CommunicationRetrievalError)
    spy = mocker.patch(
        PATCH_BENCHMARK.format("Benchmark._Benchmark__get_local_dict"),
        return_value=benchmark_dict(),
    )
    uid = benchmarks_uids[0]

    # Act
    Benchmark.get(uid)

    # Assert
    spy.assert_called_once_with(uid)


@pytest.mark.parametrize("benchmarks_uids", [[449, 66, 337]])
def test_get_benchmark_reads_remote_benchmark(mocker, comms, benchmarks_uids):
    # Arrange
    benchmarks_uids = [str(uid) for uid in benchmarks_uids]
    mocker.patch("os.listdir", return_value=benchmarks_uids)
    mocker.patch(PATCH_BENCHMARK.format("Benchmark.write"))
    spy = mocker.patch(
        PATCH_BENCHMARK.format("Benchmark._Benchmark__get_local_dict"), return_value={}
    )
    uid = benchmarks_uids[0]

    # Act
    Benchmark.get(uid)

    # Assert
    spy.assert_not_called()


@pytest.mark.parametrize("uid", [94, 23, 87])
def test_get_local_dict_reads_expected_file(mocker, comms, uid):
    # Arrange
    uid = str(uid)
    mocker.patch("os.listdir", return_value=[uid])
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("yaml.safe_load", return_value=benchmark_dict())
    spy = mocker.patch("builtins.open", mock_open())
    mocker.patch(PATCH_BENCHMARK.format("Benchmark.write"))
    mocker.patch.object(comms, "get_benchmark", side_effect=CommunicationRetrievalError)
    exp_file = os.path.join(
        storage_path(config.benchmarks_storage), uid, config.benchmarks_filename
    )

    # Act
    Benchmark.get(uid)

    # Assert
    spy.assert_called_once_with(exp_file, "r")


@pytest.mark.parametrize("data_prep", [12, 78])
@pytest.mark.parametrize("model", [654, 4])
@pytest.mark.parametrize("eval", [6, 354])
def test_tmp_creates_and_writes_temporary_benchmark(mocker, data_prep, model, eval):
    # Arrange
    data_prep = str(data_prep)
    model = str(model)
    eval = str(eval)
    write_spy = mocker.patch(PATCH_BENCHMARK.format("Benchmark.write"))
    init_spy = mocker.spy(Benchmark, "__init__")

    # Act
    benchmark = Benchmark.tmp(data_prep, model, eval)

    # Assert
    init_spy.assert_called_once()
    write_spy.assert_called_once()
    assert benchmark.data_preparation == data_prep
    assert benchmark.reference_model == model
    assert benchmark.evaluator == eval


def test_benchmark_includes_reference_model_in_models(comms, no_local):
    # Act
    uid = 1
    benchmark = Benchmark.get(uid)

    # Assert
    assert benchmark.reference_model in benchmark.models


@pytest.mark.parametrize(
    "models",
    [[4975, 573, 269, 3172], [556, 1588, 3398, 2724], [3531, 1423, 2275, 4223]],
)
def test_benchmark_includes_additional_models_in_models(
    mocker, comms, models, no_local
):
    # Arrange
    mocker.patch.object(comms, "get_benchmark_models", return_value=models)

    # Act
    uid = 1
    benchmark = Benchmark.get(uid)

    # Assert
    assert set(models).issubset(set(benchmark.models))


def test_write_writes_to_expected_file(mocker, comms):
    # Arrange
    uid = 1
    mocker.patch("os.listdir", return_value=[])
    mocker.patch("os.path.exists", return_value=True)
    open_spy = mocker.patch("builtins.open", mock_open())
    yaml_spy = mocker.patch("yaml.dump")
    exp_file = os.path.join(
        storage_path(config.benchmarks_storage), str(uid), config.benchmarks_filename
    )

    # Act
    benchmark = Benchmark.get("1")
    benchmark.write()

    # Assert
    open_spy.assert_any_call(exp_file, "w")
    yaml_spy.assert_any_call(benchmark.todict(), ANY)
