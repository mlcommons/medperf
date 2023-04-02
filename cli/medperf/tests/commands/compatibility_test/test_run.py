from medperf.exceptions import InvalidArgumentError
import pytest

from medperf.commands.compatibility_test.run import CompatibilityTestExecution
from .params_cases import INVALID_EXAMPLES, VALID_EXAMPLES
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.entities.utils import setup_benchmark_comms


@pytest.fixture
def exec_instance(request):
    return CompatibilityTestExecution(**request.param)


class TestValidate:
    @pytest.mark.parametrize("exec_instance", INVALID_EXAMPLES, indirect=True)
    def test_InvalidArgumentError_is_raised_for_invalid_inputs(mocker, exec_instance):
        with pytest.raises(InvalidArgumentError):
            exec_instance.validate()

    @pytest.mark.parametrize("exec_instance", VALID_EXAMPLES, indirect=True)
    def test_no_exception_raised_for_valid_inputs(mocker, exec_instance):
        exec_instance.validate()


@pytest.mark.parametrize("exec_instance", [{"benchmark": 1}], indirect=True)
class TestProcessBenchmark:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, mocker, exec_instance, comms):
        self.benchmark = TestBenchmark(id=exec_instance.benchmark_uid)
        setup_benchmark_comms(mocker, comms, [self.benchmark.todict()], [], [])
        self.benchmark_get_spy = mocker.patch(
            "medperf.entities.benchmark.Benchmark.get", return_value=self.benchmark
        )

    @pytest.mark.parametrize("benchmark_uid,offline", [[1, False], [2, True]])
    def test_BenchmarkGet_is_called_correctly(
        self, mocker, exec_instance, benchmark_uid, offline
    ):
        # Arrange
        exec_instance.offline = offline
        exec_instance.benchmark_uid = benchmark_uid

        # Act
        exec_instance.process_benchmark()

        # Assert
        self.benchmark_get_spy.assert_called_once_with(
            benchmark_uid, local_only=offline
        )

    def test_cubes_are_set_from_benchmark_when_missing(self, mocker, exec_instance):
        # Act
        exec_instance.process_benchmark()

        # Assert
        assert exec_instance.model is self.benchmark.reference_model_mlcube
        assert exec_instance.evaluator is self.benchmark.data_evaluator_mlcube

    @pytest.mark.parametrize("data_source", ["path", "demo", "benchmark"])
    def test_prep_cube_is_set_from_benchmark_when_missing(
        self, mocker, exec_instance, data_source
    ):
        # Arrange
        exec_instance.data_source = data_source

        # Act
        exec_instance.process_benchmark()

        # Assert
        assert exec_instance.data_prep is self.benchmark.data_preparation_mlcube

    def test_prep_cube_is_not_set_from_benchmark_when_not_needed(
        self, mocker, exec_instance
    ):
        # Arrange
        exec_instance.data_source = "prepared"

        # Act
        exec_instance.process_benchmark()

        # Assert
        assert exec_instance.data_prep != self.benchmark.data_preparation_mlcube

    @pytest.mark.parametrize("data_source", ["path", "demo", "benchmark"])
    def test_cubes_are_not_set_from_benchmark_when_provided(
        self, mocker, exec_instance, data_source
    ):
        # Arrange
        exec_instance.data_source = data_source
        exec_instance.data_prep = "original prep"
        exec_instance.model = "original model"
        exec_instance.evaluator = "original eval"

        # Act
        exec_instance.process_benchmark()

        # Assert
        assert exec_instance.data_prep != self.benchmark.data_preparation_mlcube
        assert exec_instance.model != self.benchmark.reference_model_mlcube
        assert exec_instance.evaluator != self.benchmark.data_evaluator_mlcube

    def test_demo_info_set_from_benchmark_when_datasource_is_benchmark(
        self, mocker, exec_instance
    ):
        # Arrange
        exec_instance.data_source = "benchmark"

        # Act
        exec_instance.process_benchmark()

        # Assert
        assert exec_instance.demo_dataset_url is self.benchmark.demo_dataset_tarball_url
        assert (
            exec_instance.demo_dataset_hash is self.benchmark.demo_dataset_tarball_hash
        )

