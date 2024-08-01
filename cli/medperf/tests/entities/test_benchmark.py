import pytest

from medperf.entities.benchmark import Benchmark
from medperf.tests.entities.utils import setup_benchmark_fs, setup_benchmark_comms


PATCH_BENCHMARK = "medperf.entities.benchmark.{}"


@pytest.fixture(
    params={
        "unregistered": ["b1", "b2"],
        "local": ["b1", "b2", 1, 2, 3],
        "remote": [1, 2, 3, 4, 5, 6],
        "user": [4],
        "models": [10, 11],
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
    mocker.patch.object(comms, "get_benchmark_model_associations", return_value=models)
    request.param["uploaded"] = uploaded

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
        id = setup["remote"][0]

        # Act
        assciated_models = Benchmark.get_models_uids(id)

        # Assert
        assert set(assciated_models) == set(expected_models)
