from medperf.exceptions import InvalidArgumentError
import pytest

from medperf.commands.compatibility_test.run import CompatibilityTestExecution
from .params_cases import (
    INVALID_EXAMPLES,
    DATA_FROM_PATH_EXAMPLES,
    DATA_FROM_DEMO_EXAMPLES,
    DATA_FROM_PREPARED_EXAMPLES,
    DATA_FROM_BENCHMARK_EXAMPLES,
)
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.entities.utils import setup_benchmark_comms, setup_benchmark_fs


class TestValidate:
    @pytest.fixture(autouse=True)
    def setup(self, request):
        self.exec_instance = CompatibilityTestExecution(**request.param)

    @pytest.mark.parametrize("setup", INVALID_EXAMPLES, indirect=True)
    def test_InvalidArgumentError_is_raised_for_invalid_inputs(self):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            self.exec_instance.validate()

    @pytest.mark.parametrize("setup", DATA_FROM_PATH_EXAMPLES, indirect=True)
    def test_valid_examples_with_data_from_paths(self):
        # Act
        self.exec_instance.validate()

        # Assert
        assert self.exec_instance.data_source == "path"

    @pytest.mark.parametrize("setup", DATA_FROM_DEMO_EXAMPLES, indirect=True)
    def test_valid_examples_with_demo_data_input(self):
        # Act
        self.exec_instance.validate()

        # Assert
        assert self.exec_instance.data_source == "demo"

    @pytest.mark.parametrize("setup", DATA_FROM_PREPARED_EXAMPLES, indirect=True)
    def test_valid_examples_with_prepared_data_input(self):
        # Act
        self.exec_instance.validate()

        # Assert
        assert self.exec_instance.data_source == "prepared"

    @pytest.mark.parametrize("setup", DATA_FROM_BENCHMARK_EXAMPLES, indirect=True)
    def test_valid_examples_with_data_from_benchmark(self):
        # Act
        self.exec_instance.validate()

        # Assert
        assert self.exec_instance.data_source == "benchmark"


class TestProcessBenchmark:
    @pytest.fixture(autouse=True)
    def setup(self, mocker, comms, fs):
        benchmark_args = {
            "id": 1,
            "data_preparation_mlcube": 1,
            "reference_model_mlcube": 2,
            "data_evaluator_mlcube": 3,
            "demo_dataset_tarball_url": "demo_url",
            "demo_dataset_tarball_hash": "demo_hash",
        }
        benchmark = TestBenchmark(**benchmark_args)

        setup_benchmark_comms(mocker, comms, [benchmark.todict()], [], [])
        setup_benchmark_fs([benchmark.todict()], fs)

        self.comms = comms
        self.benchmark = benchmark
        self.exec_instance = CompatibilityTestExecution(benchmark=1)

    def test_benchmark_is_retrieved_from_comms_by_default(self):
        # Act
        self.exec_instance.process_benchmark()

        # Assert
        self.comms.get_benchmark.assert_called_once()

    def test_benchmark_is_not_retrieved_if_not_provided(self):
        # Arrange
        self.exec_instance.benchmark_uid = None

        # Act
        self.exec_instance.process_benchmark()

        # Assert
        self.comms.get_benchmark.assert_not_called()

    def test_benchmark_is_not_retrieved_from_comms_in_offline_mode(self):
        # Arrange
        self.exec_instance.offline = True

        # Act
        self.exec_instance.process_benchmark()

        # Assert
        self.comms.get_benchmark.assert_not_called()

    def test_cubes_are_set_from_benchmark_when_missing(self):
        # Act
        self.exec_instance.process_benchmark()

        # Assert
        assert self.exec_instance.model is self.benchmark.reference_model_mlcube
        assert self.exec_instance.evaluator is self.benchmark.data_evaluator_mlcube

    @pytest.mark.parametrize("data_source", ["path", "demo", "benchmark"])
    def test_prep_cube_is_set_from_benchmark_when_missing(self, data_source):
        # Arrange
        self.exec_instance.data_source = data_source

        # Act
        self.exec_instance.process_benchmark()

        # Assert
        assert self.exec_instance.data_prep is self.benchmark.data_preparation_mlcube

    def test_prep_cube_is_not_set_from_benchmark_when_not_needed(self):
        # Arrange
        self.exec_instance.data_source = "prepared"

        # Act
        self.exec_instance.process_benchmark()

        # Assert
        assert self.exec_instance.data_prep != self.benchmark.data_preparation_mlcube

    @pytest.mark.parametrize("data_source", ["path", "demo", "benchmark"])
    def test_cubes_are_not_set_from_benchmark_when_provided(self, data_source):
        # Arrange
        self.exec_instance.data_source = data_source
        self.exec_instance.data_prep = "original prep"
        self.exec_instance.model = "original model"
        self.exec_instance.evaluator = "original eval"

        # Act
        self.exec_instance.process_benchmark()

        # Assert
        assert self.exec_instance.data_prep != self.benchmark.data_preparation_mlcube
        assert self.exec_instance.model != self.benchmark.reference_model_mlcube
        assert self.exec_instance.evaluator != self.benchmark.data_evaluator_mlcube

    def test_demo_info_set_from_benchmark_when_data_source_is_benchmark(self):
        # Arrange
        self.exec_instance.data_source = "benchmark"

        # Act
        self.exec_instance.process_benchmark()

        # Assert
        assert (
            self.exec_instance.demo_dataset_url
            is self.benchmark.demo_dataset_tarball_url
        )
        assert (
            self.exec_instance.demo_dataset_hash
            is self.benchmark.demo_dataset_tarball_hash
        )
