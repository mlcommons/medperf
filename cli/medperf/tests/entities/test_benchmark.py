import pytest

import medperf.config as config
from medperf.comms.interface import Comms
from medperf.entities.benchmark import Benchmark
from medperf.tests.mocks.requests import benchmark_body
from medperf.tests.entities.utils import setup_benchmark_fs, setup_benchmark_comms


PATCH_BENCHMARK = "medperf.entities.benchmark.{}"


@pytest.fixture(params={"local": [1, 2, 3], "remote": [4, 5, 6], "user": [4]})
def setup(request, mocker, comms, fs):
    local_ids = request.param.get("local", [])
    remote_ids = request.param.get("remote", [])
    user_ids = request.param.get("user", [])
    # Have a list that will contain all uploaded entities of the given type
    uploaded = []

    setup_benchmark_fs(local_ids, fs)
    setup_benchmark_comms(mocker, comms, remote_ids, user_ids, uploaded)
    request.param["uploaded"] = uploaded

    return request.param


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


@pytest.mark.parametrize(
    "setup", [{"local": [], "remote": ["27", "1", "2"], "user": ["2"]}], indirect=True,
)
def test_benchmark_includes_reference_model_in_models(setup):
    # Act
    id = setup["remote"][0]
    benchmark = Benchmark.get(id)

    # Assert
    assert benchmark.reference_model in benchmark.models


@pytest.mark.parametrize(
    "models",
    [[4975, 573, 269, 3172], [556, 1588, 3398, 2724], [3531, 1423, 2275, 4223]],
)
@pytest.mark.parametrize(
    "setup", [{"local": [], "remote": ["27", "1", "2"], "user": ["2"]}], indirect=True,
)
def test_benchmark_includes_additional_models_in_models(mocker, comms, models, setup):
    # Arrange
    id = setup["remote"][0]
    mocker.patch.object(comms, "get_benchmark_models", return_value=models)

    # Act
    benchmark = Benchmark.get(id)

    # Assert
    assert set(models).issubset(set(benchmark.models))
