import os
from unittest.mock import ANY, call
from medperf.commands.execution import Execution
from medperf.exceptions import ExecutionError
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
import pytest
from medperf import config
import yaml


PATCH_EXECUTION = "medperf.commands.execution.{}"


INPUT_DATASET = TestDataset()
INPUT_MODEL = TestCube(id=2)
INPUT_EVALUATOR = TestCube(id=3)


def mock_model(mocker, fs, state_variables):
    failing_model = state_variables["failing_model"]

    def _side_effect(*args, **kwargs):
        out_path = kwargs["mounts"]["output_path"]
        fs.create_dir(out_path)
        if failing_model:
            raise ExecutionError

    spy = mocker.patch.object(INPUT_MODEL, "run", side_effect=_side_effect)
    return spy


def mock_eval(mocker, fs, state_variables):
    failing_eval = state_variables["failing_eval"]
    execution_results = state_variables["execution_results"]

    def _side_effect(*args, **kwargs):
        if failing_eval:
            raise ExecutionError
        out_path = kwargs["mounts"]["output_path"]
        fs.create_file(out_path, contents=yaml.dump(execution_results))

    spy = mocker.patch.object(INPUT_EVALUATOR, "run", side_effect=_side_effect)
    return spy


@pytest.fixture()
def setup(request, mocker, ui, fs):
    # system inputs
    state_variables = {
        "failing_model": False,
        "failing_eval": False,
        "execution_results": {"res": 1, "metric": 55},
        "result_path": "tmp_result_path",
    }
    state_variables.update(request.param)

    # mocks/spies
    model_run_spy = mock_model(mocker, fs, state_variables)
    eval_run_spy = mock_eval(mocker, fs, state_variables)

    mocker.patch(
        PATCH_EXECUTION.format("generate_tmp_path"),
        return_value=state_variables["result_path"],
    )
    spies = {
        "model_run": model_run_spy,
        "eval_run": eval_run_spy,
    }
    return state_variables, spies


class TestFailures:
    @pytest.mark.parametrize(
        "setup", [{"failing_model": True}, {"failing_eval": True}], indirect=True
    )
    def test_failure_with_failing_cubes_and_no_ignore_error(mocker, setup):
        # Act & Assert
        with pytest.raises(ExecutionError):
            Execution.run(
                INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, ignore_model_errors=False
            )

    @pytest.mark.parametrize("setup", [{"failing_eval": True}], indirect=True)
    def test_failure_with_failing_eval_and_ignore_error(mocker, setup):
        # Act & Assert
        with pytest.raises(ExecutionError):
            Execution.run(
                INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, ignore_model_errors=True
            )

    @pytest.mark.parametrize("setup", [{"failing_model": True}], indirect=True)
    def test_no_failure_with_ignore_error(mocker, setup):
        # Act & Assert
        Execution.run(
            INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, ignore_model_errors=True
        )

    @pytest.mark.parametrize("setup", [{}], indirect=True)
    @pytest.mark.parametrize("ignore_model_errors", [True, False])
    def test_failure_with_existing_predictions(mocker, setup, ignore_model_errors, fs):
        # Arrange
        preds_path = os.path.join(
            config.predictions_folder,
            INPUT_MODEL.local_id,
            INPUT_DATASET.local_id,
        )

        fs.create_dir(preds_path)
        # Act & Assert
        with pytest.raises(ExecutionError):
            Execution.run(
                INPUT_DATASET,
                INPUT_MODEL,
                INPUT_EVALUATOR,
                ignore_model_errors=ignore_model_errors,
            )


@pytest.mark.parametrize("setup", [{"failing_model": True}], indirect=True)
def test_partial_result_when_ignore_error_and_failing_model(mocker, setup):
    # Act
    execution_summary = Execution.run(
        INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, ignore_model_errors=True
    )
    # Assert
    assert execution_summary["partial"]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_no_partial_result_by_default(mocker, setup):
    # Act
    execution_summary = Execution.run(INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR)
    # Assert
    assert not execution_summary["partial"]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_results_are_returned(mocker, setup):
    # Act
    execution_summary = Execution.run(INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR)
    # Assert
    state_variables = setup[0]
    assert execution_summary["results"] == state_variables["execution_results"]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_cube_run_are_called_properly(mocker, setup):
    # Arrange
    exp_preds_path = os.path.join(
        config.predictions_folder,
        INPUT_MODEL.local_id,
        INPUT_DATASET.local_id,
    )

    exp_model_logs_path = os.path.join(
        config.experiments_logs_folder,
        INPUT_MODEL.local_id,
        INPUT_DATASET.local_id,
        "model.log",
    )

    exp_metrics_logs_path = os.path.join(
        config.experiments_logs_folder,
        INPUT_MODEL.local_id,
        INPUT_DATASET.local_id,
        f"metrics_{INPUT_EVALUATOR.local_id}.log",
    )

    exp_model_call = call(
        task="infer",
        output_logs=exp_model_logs_path,
        timeout=config.infer_timeout,
        mounts={
            "data_path": INPUT_DATASET.data_path,
            "output_path": exp_preds_path,
        },
    )
    exp_eval_call = call(
        task="evaluate",
        output_logs=exp_metrics_logs_path,
        timeout=config.evaluate_timeout,
        mounts={
            "predictions": exp_preds_path,
            "labels": INPUT_DATASET.labels_path,
            "output_path": ANY,
        },
    )
    # Act
    Execution.run(INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR)
    # Assert
    spies = setup[1]
    spies["model_run"].assert_has_calls([exp_model_call])
    spies["eval_run"].assert_has_calls([exp_eval_call])
    spies["model_run"].assert_called_once()
    spies["eval_run"].assert_called_once()
