import os
from medperf import config
from medperf.exceptions import ExecutionError, InvalidArgumentError
from medperf.tests.mocks.result import TestResult
import pytest
from unittest.mock import MagicMock, call

from medperf.utils import storage_path
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.commands.result.create import BenchmarkExecution

PATCH_EXECUTION = "medperf.commands.result.create.{}"


@pytest.fixture
def execution(mocker, comms, ui):
    mock_dset = TestDataset(id=1, generated_uid="gen_uid")
    mock_bmark = TestBenchmark(id=1)
    mocker.patch(PATCH_EXECUTION.format("init_storage"))
    mocker.patch(PATCH_EXECUTION.format("Dataset"), side_effect=mock_dset)
    mocker.patch("medperf.entities.result.Dataset.get", return_value=mock_dset)
    mocker.patch(PATCH_EXECUTION.format("Benchmark"), side_effect=mock_bmark)
    exec = BenchmarkExecution(0, 0, 0)
    exec.prepare()
    exec.out_path = "out_path"
    exec.dataset.id = 1
    exec.dataset.generated_uid = "data_uid"
    exec.dataset.data_preparation_mlcube = "prep_cube"
    exec.dataset.labels_path = "labels_path"
    exec.benchmark.data_preparation_mlcube = "prep_cube"
    exec.benchmark.models = [0]
    exec.evaluator = TestCube(id=3)
    exec.model_cube = TestCube(id=2)
    return exec


def test_validate_fails_if_preparation_cube_mismatch(mocker, execution):
    # Arrange
    execution.dataset.preparation_cube_uid = "dset_prep_cube"
    execution.benchmark.data_preparation = "bmark_prep_cube"

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        execution.validate()


@pytest.mark.parametrize("model_uid", [4559, 3292, 1499])
def test_validate_fails_if_model_not_in_benchmark(mocker, execution, model_uid):
    # Arrange
    execution.model_uid = model_uid  # model not in benchmark

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        execution.validate()


def test_validate_fails_if_dataset_is_not_registered(mocker, execution):
    # Arrange
    execution.dataset.uid = None

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        execution.validate()


def test_validate_passes_under_right_conditions(mocker, execution):
    # Act & Assert
    execution.validate()


@pytest.mark.parametrize("evaluator_uid", [1965, 2164])
@pytest.mark.parametrize("model_uid", [3791, 2383])
def test_get_cubes_retrieves_expected_cubes(
    mocker, execution, evaluator_uid, model_uid
):
    # Arrange
    spy = mocker.patch(
        PATCH_EXECUTION.format("BenchmarkExecution._BenchmarkExecution__get_cube")
    )
    execution.benchmark.data_evaluator_mlcube = evaluator_uid
    execution.model_uid = model_uid
    evaluator_call = call(evaluator_uid, "Evaluator")
    model_call = call(model_uid, "Model")
    calls = [evaluator_call, model_call]

    # Act
    execution.get_cubes()

    # Assert
    spy.assert_has_calls(calls)


@pytest.mark.parametrize("cube_uid", [3889, 4669])
def test__get_cube_retrieves_cube(mocker, execution, cube_uid):
    # Arrange
    name = "872"
    spy = mocker.patch(PATCH_EXECUTION.format("Cube.get"))
    mocker.patch(PATCH_EXECUTION.format("check_cube_validity"))

    # Act
    execution._BenchmarkExecution__get_cube(cube_uid, name)

    # Assert
    spy.assert_called_once_with(cube_uid)


def test__get_cube_checks_cube_validity(mocker, execution, cube):
    # Arrange
    mocker.patch(PATCH_EXECUTION.format("Cube.get"), return_value=cube)
    spy = mocker.patch(PATCH_EXECUTION.format("check_cube_validity"))

    # Act
    execution._BenchmarkExecution__get_cube(1, "test")

    # Assert
    spy.assert_called_once_with(cube)


def test_run_cubes_executes_expected_cube_tasks(mocker, execution):
    # Arrange
    data_path = "data_path"
    labels_path = "labels_path"
    cube_path = "cube_path"
    model_uid = str(execution.model_cube.id)
    data_uid = str(execution.dataset.id)
    preds_path = os.path.join(config.predictions_storage, model_uid, data_uid)
    preds_path = storage_path(preds_path)
    result_path = os.path.join(execution.out_path, config.results_filename)
    execution.dataset.data_path = data_path
    execution.dataset.labels_path = labels_path
    execution.model_cube.cube_path = cube_path
    model_spy = mocker.patch.object(execution.model_cube, "run")
    eval_spy = mocker.patch.object(execution.evaluator, "run")
    infer = call(
        task="infer",
        timeout=None,
        data_path="data_path",
        output_path=preds_path,
        string_params={"Ptasks.infer.parameters.input.data_path.opts": "ro",},
    )
    evaluate = call(
        task="evaluate",
        timeout=None,
        predictions=preds_path,
        labels="labels_path",
        output_path=result_path,
        string_params={
            "Ptasks.evaluate.parameters.input.predictions.opts": "ro",
            "Ptasks.evaluate.parameters.input.labels.opts": "ro",
        },
    )

    # Act
    execution.run_cubes()

    # Assert
    model_spy.assert_has_calls([infer])
    eval_spy.assert_has_calls([evaluate])


def test_run_executes_expected_flow(mocker, comms, ui, execution):
    # Arrange
    prep_spy = mocker.patch(PATCH_EXECUTION.format("BenchmarkExecution.prepare"))
    val_spy = mocker.patch(PATCH_EXECUTION.format("BenchmarkExecution.validate"))
    get_spy = mocker.patch(PATCH_EXECUTION.format("BenchmarkExecution.get_cubes"))
    run_spy = mocker.patch(PATCH_EXECUTION.format("BenchmarkExecution.run_cubes"))
    write_spy = mocker.patch(PATCH_EXECUTION.format("BenchmarkExecution.write"))
    remove_spy = mocker.patch(
        PATCH_EXECUTION.format("BenchmarkExecution.remove_temp_results")
    )

    # Act
    BenchmarkExecution.run(1, 1, 1)

    # Assert
    prep_spy.assert_called_once()
    val_spy.assert_called_once()
    get_spy.assert_called_once()
    run_spy.assert_called_once()
    write_spy.assert_called_once()
    remove_spy.assert_called_once()


@pytest.mark.parametrize("mlcube", ["model", "eval"])
def test_run_deletes_output_path_on_failure(mocker, execution, mlcube):
    # Arrange
    execution.dataset.data_path = "data_path"
    execution.model_cube.cube_path = "cube_path"
    out_path = "out_path"
    preds_path = "preds_path"

    if mlcube == "model":
        failed_cube = execution.model_cube
        exp_outpaths = [preds_path]
    else:
        failed_cube = execution.evaluator
        exp_outpaths = [preds_path, os.path.join(out_path, config.results_filename)]

    mocker.patch.object(
        failed_cube, "run", side_effect=ExecutionError,
    )
    mocker.patch(
        PATCH_EXECUTION.format("storage_path"), return_value=preds_path,
    )
    spy_clean = mocker.patch(PATCH_EXECUTION.format("cleanup"))

    # Act & Assert
    with pytest.raises(ExecutionError):
        execution.run_cubes()

    spy_clean.assert_called_once_with(exp_outpaths)


def test_todict_calls_get_temp_results(mocker, execution):
    # Arrange
    spy = mocker.patch(PATCH_EXECUTION.format("BenchmarkExecution.get_temp_results"))
    # Act
    execution.todict()

    # Assert
    spy.assert_called_once()


def test_write_calls_result_write(mocker, execution):
    # Arrange
    result_info = TestResult().todict()
    mocker.patch(
        PATCH_EXECUTION.format("BenchmarkExecution.todict"), return_value=result_info
    )
    spy = mocker.patch(PATCH_EXECUTION.format("Result.write"))
    # Act
    execution.write()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("path", ["res_path", "path/to/folder"])
def test_get_temp_results_opens_results_path(mocker, path, execution):
    # Arrange
    execution.out_path = path
    spy = mocker.patch("builtins.open", MagicMock())
    mocker.patch(PATCH_EXECUTION.format("yaml.safe_load"), return_value={})
    opened_path = os.path.join(path, config.results_filename)
    # Act
    execution.get_temp_results()

    # Assert
    spy.assert_called_once_with(opened_path, "r")


@pytest.mark.parametrize("path", ["res_path", "path/to/folder"])
def test_remove_temp_results_removes_file(mocker, path, execution):
    # Arrange
    execution.out_path = path
    spy = mocker.patch(PATCH_EXECUTION.format("os.remove"))
    deleted = os.path.join(path, config.results_filename)
    # Act
    execution.remove_temp_results()

    # Assert
    spy.assert_called_once_with(deleted)


@pytest.mark.parametrize("ignore_errors", [False, True])
@pytest.mark.parametrize("mlcube", ["model", "eval"])
def test_run_cubes_ignore_errors_if_specified(mocker, execution, mlcube, ignore_errors):
    # Arrange
    execution.dataset.data_path = "data_path"
    execution.model_cube.cube_path = "cube_path"
    execution.ignore_errors = ignore_errors
    preds_path = "preds_path"

    if mlcube == "model":
        failed_cube = execution.model_cube
    else:
        failed_cube = execution.evaluator

    mocker.patch.object(
        failed_cube, "run", side_effect=ExecutionError,
    )
    mocker.patch(
        PATCH_EXECUTION.format("storage_path"), return_value=preds_path,
    )
    mocker.patch(PATCH_EXECUTION.format("cleanup"))

    # Act & Assert

    # Assert
    if ignore_errors:
        execution.run_cubes()
    else:
        with pytest.raises(ExecutionError):
            execution.run_cubes()
    assert execution.metadata["partial"] == ignore_errors
