from unittest.mock import ANY
from medperf.exceptions import InvalidArgumentError
from medperf.tests.mocks.report import TestTestReport
from medperf.tests.mocks.cube import TestCube
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

PATCH_RUN = "medperf.commands.compatibility_test.run.{}"


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
        self.exec_instance.set_data_source()

        # Assert
        assert self.exec_instance.data_source == "path"

    @pytest.mark.parametrize("setup", DATA_FROM_DEMO_EXAMPLES, indirect=True)
    def test_valid_examples_with_demo_data_input(self):
        # Act
        self.exec_instance.validate()
        self.exec_instance.set_data_source()

        # Assert
        assert self.exec_instance.data_source == "demo"

    @pytest.mark.parametrize("setup", DATA_FROM_PREPARED_EXAMPLES, indirect=True)
    def test_valid_examples_with_prepared_data_input(self):
        # Act
        self.exec_instance.validate()
        self.exec_instance.set_data_source()

        # Assert
        assert self.exec_instance.data_source == "prepared"

    @pytest.mark.parametrize("setup", DATA_FROM_BENCHMARK_EXAMPLES, indirect=True)
    def test_valid_examples_with_data_from_benchmark(self):
        # Act
        self.exec_instance.validate()
        self.exec_instance.set_data_source()

        # Assert
        assert self.exec_instance.data_source == "benchmark"


class TestProcessBenchmark:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        benchmark_data = {
            "id": 1,
            "data_preparation_mlcube": 1,
            "reference_model_mlcube": 2,
            "data_evaluator_mlcube": 3,
            "demo_dataset_tarball_url": "demo_url",
            "demo_dataset_tarball_hash": "demo_hash",
        }
        benchmark = TestBenchmark(**benchmark_data)
        spy = mocker.patch(PATCH_RUN.format("Benchmark.get"), return_value=benchmark)

        self.benchmark_get_spy = spy
        self.exec_instance = CompatibilityTestExecution(benchmark=benchmark.id)
        self.benchmark = benchmark

    @pytest.mark.parametrize("offline", [True, False])
    def test_benchmark_is_retrieved_according_to_offline_param(self, offline):
        # Arrange
        self.exec_instance.offline = offline

        # Act
        self.exec_instance.process_benchmark()

        # Assert
        self.benchmark_get_spy.assert_called_once_with(
            self.benchmark.id, local_only=offline
        )

    def test_benchmark_is_not_retrieved_if_not_provided(self):
        # Arrange
        self.exec_instance.benchmark_uid = None

        # Act
        self.exec_instance.process_benchmark()

        # Assert
        self.benchmark_get_spy.assert_not_called()

    def test_model_and_eval_cubes_are_set_from_benchmark_when_missing(self):
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


class TestPrepareCubes:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.prep_uid = 1
        self.model_uid = 2
        self.eval_uid = 3

        self.new_prep_uid = "new_prep"
        self.new_model_uid = "new_model"
        self.new_eval_uid = "new_eval"

        overriding_cubes = [
            TestCube(id=None, name="new_prep"),
            TestCube(id=None, name="new_model"),
            TestCube(id=None, name="new_eval"),
        ]
        self.prepare_spy = mocker.patch(
            PATCH_RUN.format("prepare_cube"),
            side_effect=overriding_cubes,
        )

        self.exec_instance = CompatibilityTestExecution(
            data_prep=self.prep_uid, model=self.model_uid, evaluator=self.eval_uid
        )

    @pytest.mark.parametrize("data_source", ["path", "demo", "benchmark"])
    def test_cube_uids_are_prepared(self, mocker, data_source):
        # Arrange
        self.exec_instance.data_source = data_source

        # Act
        self.exec_instance.prepare_cubes()

        # Assert
        calls = self.prepare_spy.call_args_list
        assert len(calls) == 3
        assert calls[0][0][0] == self.prep_uid  # First call, first positional arg
        assert calls[1][0][0] == self.model_uid  # Second call, first positional arg
        assert calls[2][0][0] == self.eval_uid  # Third call, first positional arg

        assert self.exec_instance.data_prep_cube.identifier == self.new_prep_uid
        assert self.exec_instance.model_cube.identifier == self.new_model_uid
        assert self.exec_instance.evaluator_cube.identifier == self.new_eval_uid

    def test_prep_cube_is_not_prepared_if_data_is_prepared(self, mocker):
        # Arrange
        exec_instance = CompatibilityTestExecution(data_prep=1)
        exec_instance.data_source = "prepared"

        spy = mocker.patch(PATCH_RUN.format("prepare_cube"))

        # Act
        exec_instance.prepare_cubes()

        # Assert
        assert spy.call_count == 2


class TestPrepareDataset:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.exec_instance = CompatibilityTestExecution()
        mock_cube = TestCube(is_valid=True)
        mocker.patch(PATCH_RUN.format("Dataset.get"))
        mocker.patch("medperf.entities.cube.Cube.get", return_value=mock_cube)
        self.new_data_uid = "new prepared data uid"
        self.prepare_spy = mocker.patch(
            PATCH_RUN.format("create_test_dataset"), return_value=self.new_data_uid
        )

    def test_data_preparation_is_not_run_when_prepared_data_is_provided(self):
        # Arrange
        data_uid = "provided_data_uid"
        self.exec_instance.data_uid = data_uid
        self.exec_instance.data_source = "prepared"

        # Act
        self.exec_instance.prepare_dataset()

        # Assert
        self.prepare_spy.assert_not_called()

    @pytest.mark.parametrize("offline", [True, False])
    def test_dataset_is_retrieved_correctly(self, mocker, offline):
        # Arrange
        data_uid = "provided_data_uid"
        self.exec_instance.data_uid = data_uid
        self.exec_instance.data_source = "prepared"
        self.exec_instance.offline = offline

        get_spy = mocker.patch(PATCH_RUN.format("Dataset.get"))

        # Act
        self.exec_instance.prepare_dataset()

        # Assert
        get_spy.assert_called_once_with(data_uid, local_only=offline)

    def test_data_is_prepared_using_provided_datapath_and_labels(self, fs):
        # Arrange
        data_path = "path/to/data"
        labels_path = "path/to/labels"
        self.exec_instance.data_path = data_path
        self.exec_instance.labels_path = labels_path
        self.exec_instance.data_source = "path"
        self.exec_instance.data_prep = 1

        # Act
        self.exec_instance.prepare_dataset()

        # Assert
        self.prepare_spy.assert_called_once_with(
            data_path, labels_path, None, ANY, False
        )
        assert self.exec_instance.data_uid == self.new_data_uid

    @pytest.mark.parametrize("data_source", ["demo", "benchmark"])
    def test_data_is_prepared_using_provided_demo_dset(self, mocker, data_source):
        # Arrange
        demo_url = "demo_url"
        demo_hash = "demo_hash"
        data_path = "path/to/prepared demo data"
        labels_path = "path/to/prepared demo labels"
        metadata_path = "path/to/metadata"
        self.exec_instance.demo_dataset_url = demo_url
        self.exec_instance.demo_dataset_hash = demo_hash
        self.exec_instance.data_source = data_source
        download_demo_spy = mocker.patch(
            PATCH_RUN.format("download_demo_data"),
            return_value=[data_path, labels_path, metadata_path],
        )

        # Act
        self.exec_instance.prepare_dataset()

        # Assert
        self.prepare_spy.assert_called_once_with(
            data_path, labels_path, metadata_path, ANY, False
        )
        download_demo_spy.assert_called_once_with(demo_url, demo_hash)
        assert self.exec_instance.data_uid == self.new_data_uid


class TestCachedResults:
    @pytest.fixture(autouse=True)
    def setup(self, fs):
        report = TestTestReport()
        report.write()

        self.report = report
        self.exec_instance = CompatibilityTestExecution()
        self.exec_instance.report = report

    def test_cached_results_are_returned_when_cache_is_enabled(self):
        # Arrange
        self.exec_instance.no_cache = False

        # Act
        cached_results = self.exec_instance.cached_results()

        # Assert
        assert cached_results == self.report.results

    def test_cached_results_are_none_when_cache_is_disabled(self):
        # Arrange
        self.exec_instance.no_cache = True

        # Act
        cached_results = self.exec_instance.cached_results()

        # Assert
        assert cached_results is None
