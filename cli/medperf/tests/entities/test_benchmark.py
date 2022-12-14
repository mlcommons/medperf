import os
import pytest
from unittest.mock import mock_open, ANY

import medperf.config as config
from medperf.comms.interface import Comms
from medperf.utils import storage_path
from medperf.entities.benchmark import Benchmark
from medperf.tests.mocks.requests import benchmark_body


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
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("os.makedirs")
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
