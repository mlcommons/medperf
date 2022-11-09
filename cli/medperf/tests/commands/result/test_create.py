import os
from medperf import config
from medperf.tests.mocks.requests import result_dict
import pytest
from unittest.mock import MagicMock, call

from medperf.utils import storage_path
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.commands.result.create import BenchmarkExecution

PATCH_EXECUTION = "medperf.commands.result.create.{}"


@pytest.fixture
def cube(mocker):
    def cube_gen():
        cube = mocker.create_autospec(spec=Cube)
        cube.uid = 1
        return cube

    return cube_gen


@pytest.fixture
def execution(mocker, comms, ui, cube):
    mock_dset = mocker.create_autospec(spec=Dataset)
    mock_bmark = mocker.create_autospec(spec=Benchmark)
    mocker.patch(PATCH_EXECUTION.format("init_storage"))
    mocker.patch(PATCH_EXECUTION.format("Dataset"), side_effect=mock_dset)
    mocker.patch(PATCH_EXECUTION.format("Benchmark"), side_effect=mock_bmark)
    exec = BenchmarkExecution(0, 0, 0)
    exec.prepare()
    exec.out_path = "out_path"
    exec.dataset.uid = 1
    exec.dataset.generated_uid = "data_uid"
    exec.dataset.preparation_cube_uid = "prep_cube"
    exec.dataset.labels_path = "labels_path"
    exec.benchmark.data_preparation = "prep_cube"
    exec.benchmark.models = [0]
    exec.evaluator = cube()
    exec.model_cube = cube()
    return exec


def test_validate_fails_if_preparation_cube_mismatch(mocker, execution):
    # Arrange
    execution.dataset.preparation_cube_uid = "dset_prep_cube"
    execution.benchmark.data_preparation = "bmark_prep_cube"
    spy = mocker.patch(
        PATCH_EXECUTION.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    with pytest.raises(SystemExit):
        execution.validate()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("model_uid", [4559, 3292, 1499])
def test_validate_fails_if_model_not_in_benchmark(mocker, execution, model_uid):
    # Arrange
    execution.model_uid = model_uid  # model not in benchmark
    spy = mocker.patch(
        PATCH_EXECUTION.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    with pytest.raises(SystemExit):
        execution.validate()

    # Assert
    spy.assert_called_once()


def test_validate_fails_if_dataset_is_not_registered(mocker, execution):
    # Arrange
    execution.dataset.uid = None
    spy = mocker.patch(
        PATCH_EXECUTION.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    with pytest.raises(SystemExit):
        execution.validate()

    # Assert
    spy.assert_called_once()


def test_validate_passes_under_right_conditions(mocker, execution):
    # Arrange
    spy = mocker.patch(PATCH_EXECUTION.format("pretty_error"))

    # Act
    execution.validate()

    # Assert
    spy.assert_not_called()


@pytest.mark.parametrize("evaluator_uid", [1965, 2164])
@pytest.mark.parametrize("model_uid", [3791, 2383])
def test_get_cubes_retrieves_expected_cubes(
    mocker, execution, evaluator_uid, model_uid
):
    # Arrange
    spy = mocker.patch(
        PATCH_EXECUTION.format("BenchmarkExecution._BenchmarkExecution__get_cube")
    )
    execution.benchmark.evaluator = evaluator_uid
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
    model_uid = str(execution.model_cube.uid)
    data_uid = execution.dataset.generated_uid
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
        failed_cube,
        "run",
        side_effect=lambda *args, **kwargs: exec("raise RuntimeError()"),
    )
    mocker.patch(
        PATCH_EXECUTION.format("results_path"), return_value=out_path,
    )
    mocker.patch(
        PATCH_EXECUTION.format("storage_path"), return_value=preds_path,
    )
    spy_clean = mocker.patch(PATCH_EXECUTION.format("cleanup"))
    spy_error = mocker.patch(PATCH_EXECUTION.format("pretty_error"))

    # Act
    execution.run_cubes()

    # Assert
    spy_clean.assert_called_once_with(exp_outpaths)
    spy_error.assert_called_once()


def test_todict_calls_get_temp_results(mocker, execution):
    # Arrange
    spy = mocker.patch(PATCH_EXECUTION.format("BenchmarkExecution.get_temp_results"))
    # Act
    execution.todict()

    # Assert
    spy.assert_called_once()


def test_todict_returns_expected_keys(mocker, execution):
    # Arrange
    mocker.patch(PATCH_EXECUTION.format("BenchmarkExecution.get_temp_results"))

    # Act
    keys = execution.todict().keys()

    # Assert
    assert set(keys) == set(result_dict().keys())


def test_write_calls_result_write(mocker, execution):
    # Arrange
    result_info = result_dict()
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
    out_path = "out_path"
    preds_path = "preds_path"

    if mlcube == "model":
        failed_cube = execution.model_cube
    else:
        failed_cube = execution.evaluator
    mocker.patch.object(
        failed_cube,
        "run",
        side_effect=lambda *args, **kwargs: exec("raise RuntimeError()"),
    )
    mocker.patch(
        PATCH_EXECUTION.format("results_path"), return_value=out_path,
    )
    mocker.patch(
        PATCH_EXECUTION.format("storage_path"), return_value=preds_path,
    )
    mocker.patch(PATCH_EXECUTION.format("cleanup"))
    spy_error = mocker.patch(PATCH_EXECUTION.format("pretty_error"))

    # Act
    execution.run_cubes()

    # Assert
    if ignore_errors:
        spy_error.assert_not_called()
        assert execution.metadata["partial"] is True
    else:
        spy_error.assert_called_once()
        assert execution.metadata["partial"] is False
