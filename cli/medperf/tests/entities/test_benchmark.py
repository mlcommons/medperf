import pytest

from medperf.entities.benchmark import Benchmark
from medperf.tests.entities.utils import setup_benchmark_fs, setup_benchmark_comms

PATCH_BENCHMARK = "medperf.entities.benchmark.{}"


@pytest.fixture(autouse=True)
def setup(request, mocker, comms, fs):
    local_ids = request.param.get("local", [])
    remote_ids = request.param.get("remote", [])
    user_ids = request.param.get("user", [])
    models = request.param.get("models", [])
    # Have a list that will contain all uploaded entities of the given type

    setup_benchmark_fs(local_ids, fs)
    setup_benchmark_comms(mocker, comms, remote_ids, user_ids)
    mocker.patch.object(comms, "get_benchmark_model_associations", return_value=models)

    return request.param


@pytest.mark.parametrize(
    "setup,expected_models",
    [
        (
            {
                "remote": [721],
                "models": [
                    {"model_mlcube": 37, "approval_status": "APPROVED"},
                    {"model_mlcube": 23, "approval_status": "APPROVED"},
                    {"model_mlcube": 495, "approval_status": "PENDING"},
                ],
            },
            [37, 23],
        )
    ],
    indirect=["setup"],
)
class TestModels:
    def test_benchmark_get_models_works_as_expected(self, setup, expected_models):
        # Arrange
        id_ = setup["remote"][0]

        # Act
        associated_models = Benchmark.get_models_uids(id_)

        # Assert
        assert set(associated_models) == set(expected_models)
