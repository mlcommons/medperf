import os
from unittest.mock import ANY, call
from medperf import config
from medperf.exceptions import ExecutionError, InvalidArgumentError, InvalidEntityError
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.execution import TestExecution
import pytest

from medperf.commands.execution.create import BenchmarkExecution
import medperf.commands.execution.create as create_module
import yaml


PATCH_EXECUTION = "medperf.commands.execution.create.{}"


def mock_benchmark(mocker, state_variables):
    benchmark_prep_cube = state_variables["benchmark_prep_cube"]
    benchmark_models = state_variables["benchmark_models"]
    evaluator = state_variables["evaluator"]

    def __get_side_effect(id):
        return TestBenchmark(
            id=id,
            name="bmk name",
            data_evaluator_mlcube=evaluator["uid"],
            data_preparation_mlcube=benchmark_prep_cube,
            reference_model_mlcube=benchmark_models[0],
        )

    mocker.patch(PATCH_EXECUTION.format("Benchmark.get"), side_effect=__get_side_effect)
    mocker.patch(
        PATCH_EXECUTION.format("Benchmark.get_models_uids"),
        return_value=benchmark_models[1:],
    )


def mock_dataset(mocker, state_variables):
    dataset_prep_cube = state_variables["dataset_prep_cube"]
    operational_dataset = state_variables["operational_dataset"]

    def __get_side_effect(id):
        return TestDataset(
            id=id,
            data_preparation_mlcube=dataset_prep_cube,
            state="OPERATION" if operational_dataset else "DEVELOPMENT",
        )

    mocker.patch(PATCH_EXECUTION.format("Dataset.get"), side_effect=__get_side_effect)


def mock_result_all(mocker, state_variables):
    cached_results_triplets = state_variables["cached_results_triplets"]
    results = [
        TestExecution(benchmark=triplet[0], model=triplet[1], dataset=triplet[2])
        for triplet in cached_results_triplets
    ]
    mocker.patch(
        PATCH_EXECUTION.format("get_medperf_user_data", return_value={"id": 1})
    )
    
    def __get_side_effect(unregistered: bool = False, filters: dict = {}):
        return [
            result for result in results
            if all(result.todict().get(key) == value for key, value in filters.items())
        ]

    mocker.patch(PATCH_EXECUTION.format("Execution.all"), side_effect=__get_side_effect)


def mock_cube(mocker, state_variables):
    models_props = state_variables["models_props"]
    evaluator = state_variables["evaluator"]

    def __get_side_effect(id):
        cube = TestCube(id=id)
        if cube.id == evaluator["uid"]:
            if evaluator["invalid"]:
                raise InvalidEntityError
            else:
                return cube
        if models_props[cube.id] == "invalid":
            raise InvalidEntityError
        return cube

    mocker.patch(PATCH_EXECUTION.format("Cube.get"), side_effect=__get_side_effect)
    mocker.patch(PATCH_EXECUTION.format("Cube.download_run_files"))


def mock_execution(mocker, state_variables):
    models_props = state_variables["models_props"]

    def __exec_side_effect(dataset, model, evaluator, execution, ignore_model_errors):
        if models_props[model.id] == "exec_error":
            raise ExecutionError
        return models_props[model.id]

    return mocker.patch(
        PATCH_EXECUTION.format("ExecutionFlow.run"), side_effect=__exec_side_effect
    )


@pytest.fixture()
def setup(request, mocker, ui, fs):
    # system inputs
    state_variables = {
        "benchmark_prep_cube": 1,
        "benchmark_models": [2, 4, 5, 6, 7],
        "dataset_prep_cube": 1,
        "cached_results_triplets": [[1, 2, 1], [2, 4, 1]],
        "models_props": {
            2: {
                "results": {"res": 41},
                "partial": False,
            },
            4: {
                "results": {"res": 1},
                "partial": False,
            },
            5: {
                "results": {"res": 66},
                "partial": True,
            },
            6: "exec_error",
            7: "invalid",
        },
        "evaluator": {"uid": 3, "invalid": False},
        "operational_dataset": True,
    }
    state_variables.update(request.param)

    # mocks
    mock_benchmark(mocker, state_variables)
    mock_dataset(mocker, state_variables)
    mock_result_all(mocker, state_variables)
    mock_cube(mocker, state_variables)
    exec_spy = mock_execution(mocker, state_variables)

    # spies
    ui_error_spy = mocker.patch.object(ui, "print_error")
    ui_print_spy = mocker.patch.object(ui, "print")
    tabulate_spy = mocker.spy(create_module, "tabulate")
    validate_models_spy = mocker.spy(
        create_module.BenchmarkExecution, "_BenchmarkExecution__validate_models"
    )

    spies = {
        "ui_error": ui_error_spy,
        "ui_print": ui_print_spy,
        "tabulate": tabulate_spy,
        "exec": exec_spy,
        "validate_models": validate_models_spy,
    }
    return state_variables, spies


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_failure_with_unregistered_dset(mocker, setup):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        BenchmarkExecution.run(1, data_uid=None)


@pytest.mark.parametrize("setup", [{"operational_dataset": False}], indirect=True)
def test_failure_with_development_dataset(mocker, setup):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        BenchmarkExecution.run(1, 2, models_uids=[5])
    # TODO: all of this testing style should be changed


@pytest.mark.parametrize(
    "setup", [{"benchmark_prep_cube": 11, "dataset_prep_cube": 7}], indirect=True
)
def test_failure_with_unmatching_prep(mocker, setup):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        BenchmarkExecution.run(1, 2)


@pytest.mark.parametrize(
    "setup", [{"evaluator": {"uid": 3, "invalid": True}}], indirect=True
)
def test_failure_with_invalid_eval(mocker, setup):
    # Act & Assert
    with pytest.raises(InvalidEntityError):
        BenchmarkExecution.run(1, 2)


@pytest.mark.parametrize("setup", [{}], indirect=True)
class TestInputFile:
    def test_failure_with_nonexisting_file(mocker, setup):
        # Arrange
        models_input_file = "inputs.txt"

        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            BenchmarkExecution.run(1, 2, models_input_file=models_input_file)

    def test_failure_with_invalid_content(mocker, setup, fs):
        # Arrange
        models_input_file = "inputs.txt"
        fs.create_file(models_input_file, contents="1,2,text,3")

        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            BenchmarkExecution.run(1, 2, models_input_file=models_input_file)

    def test_no_failure(mocker, setup, fs):
        # Arrange
        models_input_file = "inputs.txt"
        fs.create_file(models_input_file, contents="2,4")

        # Act & Assert
        BenchmarkExecution.run(1, 2, models_input_file=models_input_file)


@pytest.mark.parametrize("setup", [{}], indirect=True)
class TestDefaultSetup:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        state_variables, spies = setup
        self.state_variables = state_variables
        self.spies = spies

    def test_failure_with_unassociated_model(mocker, setup):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            BenchmarkExecution.run(1, 2, models_uids=[3, 10])

    @pytest.mark.parametrize("ignore_failed_experiments", [False, True])
    def test_failure_if_failed_exec_and_errors_not_ignored(
        self, mocker, setup, ignore_failed_experiments
    ):
        # Arrange
        fail_model_uid = 6
        # Act & Assert
        if not ignore_failed_experiments:
            with pytest.raises(ExecutionError):
                BenchmarkExecution.run(
                    1,
                    2,
                    models_uids=[fail_model_uid],
                    ignore_failed_experiments=False,
                )
        else:
            BenchmarkExecution.run(
                1,
                2,
                models_uids=[fail_model_uid],
                ignore_failed_experiments=True,
            )
            self.spies["ui_error"].assert_called_once()

    @pytest.mark.parametrize("ignore_failed_experiments", [False, True])
    def test_failure_if_invalid_model_and_errors_not_ignored(
        self, mocker, setup, ignore_failed_experiments
    ):
        invalid_model_uid = 7
        # Act & Assert
        if not ignore_failed_experiments:
            with pytest.raises(InvalidEntityError):
                BenchmarkExecution.run(
                    1,
                    2,
                    models_uids=[invalid_model_uid],
                    ignore_failed_experiments=False,
                )
        else:
            BenchmarkExecution.run(
                1,
                2,
                models_uids=[invalid_model_uid],
                ignore_failed_experiments=True,
            )
            self.spies["ui_error"].assert_called_once()

    @pytest.mark.parametrize("ignore_model_errors", [False, True])
    def test_execution_is_called_with_correct_ignore_model_errors(
        self, mocker, setup, ignore_model_errors
    ):
        # Act
        BenchmarkExecution.run(
            1, 2, models_uids=[5], ignore_model_errors=ignore_model_errors
        )

        # Assert
        self.spies["exec"].assert_has_calls(
            [
                call(
                    dataset=ANY,
                    model=ANY,
                    evaluator=ANY,
                    execution=ANY,
                    ignore_model_errors=ignore_model_errors,
                )
            ]
        )

    @pytest.mark.parametrize("no_cache", [False, True])
    def test_execution_not_called_with_cached_result(self, mocker, setup, no_cache):
        # Arrange
        cached_model = 2  # system inputs contains the triplet b1m2d1 as cached

        # Act
        BenchmarkExecution.run(1, 1, models_uids=[cached_model], no_cache=no_cache)

        # Assert
        if no_cache:
            self.spies["exec"].assert_called_once()
        else:
            self.spies["exec"].assert_not_called()

    @pytest.mark.parametrize("model_uid", [4, 5])
    def test_execution_of_multiple_models_with_summary(self, mocker, setup, model_uid):
        # Arrange
        exec_res = self.state_variables["models_props"][model_uid]
        headers = ["model", "local result UID", "partial result", "from cache", "error"]
        dset_uid = 2
        bmk_uid = 1
        expected_datalist = [
            [
                model_uid,
                f"b{bmk_uid}m{model_uid}d{dset_uid}",
                exec_res["partial"],
                False,
                "",
            ]
        ]
        # Act
        BenchmarkExecution.run(1, 2, models_uids=[model_uid], show_summary=True)

        # Assert
        self.spies["tabulate"].assert_called_once_with(
            expected_datalist, headers=headers
        )

    def test_execution_of_one_model_writes_result(self, mocker, setup):
        # Arrange
        model_uid = 4
        dset_uid = 2
        bmk_uid = 1
        expected_file = os.path.join(
            config.results_folder,
            f"b{bmk_uid}m{model_uid}d{dset_uid}",
            config.results_info_file,
        )
        # Act
        BenchmarkExecution.run(bmk_uid, dset_uid, models_uids=[model_uid])

        # Assert
        assert (
            yaml.safe_load(open(expected_file))["results"]
            == self.state_variables["models_props"][model_uid]["results"]
        )

    def test_execution_of_reference_model_does_not_call_validate(self, mocker, setup):
        # Arrange
        model_uid = self.state_variables["benchmark_models"][0]
        dset_uid = 2
        bmk_uid = 1

        # Act
        BenchmarkExecution.run(bmk_uid, dset_uid, models_uids=[model_uid])

        # Assert
        self.spies["validate_models"].assert_not_called()
