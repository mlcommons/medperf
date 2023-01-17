import os
import pytest

import medperf.config as config
from medperf.utils import storage_path
from medperf.entities.benchmark import Benchmark
from medperf.tests.entities.utils import setup_benchmark_fs, setup_benchmark_comms


PATCH_BENCHMARK = "medperf.entities.benchmark.{}"


@pytest.fixture(
    params={
        "local": ["1", "2", "3"],
        "remote": ["4", "5", "6"],
        "user": ["4"],
        "models": ["10, 11"],
    }
)
def setup(request, mocker, comms, fs):
    local_ids = request.param.get("local", [])
    remote_ids = request.param.get("remote", [])
    user_ids = request.param.get("user", [])
    models = request.param.get("models", [])
    # Have a list that will contain all uploaded entities of the given type
    uploaded = []

    setup_benchmark_fs(local_ids, fs)
    setup_benchmark_comms(mocker, comms, remote_ids, user_ids, uploaded)
    mocker.patch.object(comms, "get_benchmark_models", return_value=models)
    request.param["uploaded"] = uploaded

    return request.param


@pytest.mark.parametrize("data_prep,model,eval", [[12, 654, 6], [78, 4, 354]])
class TestTmp:
    def test_tmp_creates_temporary_benchmark(self, data_prep, model, eval):
        # Act
        benchmark = Benchmark.tmp(data_prep, model, eval)

        # Assert
        assert benchmark.data_preparation_mlcube == data_prep
        assert benchmark.reference_model_mlcube == model
        assert benchmark.data_evaluator_mlcube == eval

    def test_tmp_writes_temporary_benchmark(self, data_prep, model, eval):
        # Arrange
        bmk_path = storage_path(config.benchmarks_storage)

        # Act
        bmk = Benchmark.tmp(data_prep, model, eval)

        # Assert
        bmk_filepath = os.path.join(
            bmk_path, bmk.generated_uid, config.benchmarks_filename
        )
        assert os.path.exists(bmk_filepath) and os.path.isfile(bmk_filepath)


@pytest.mark.parametrize(
    "setup", [{"remote": ["721"], "models": [37, 23, 495],}], indirect=True,
)
class TestModels:
    def test_benchmark_includes_reference_model_in_models(self, setup):
        # Act
        id = setup["remote"][0]
        benchmark = Benchmark.get(id)

        # Assert
        assert benchmark.reference_model_mlcube in benchmark.models

    def test_benchmark_includes_additional_models_in_models(self, setup):
        # Arrange
        id = setup["remote"][0]
        models = setup["models"]

        # Act
        benchmark = Benchmark.get(id)

        # Assert
        assert set(models).issubset(set(benchmark.models))
