import os
from unittest.mock import ANY, call
from medperf.commands.execution.execution_flow import ExecutionFlow
from medperf.exceptions import ExecutionError
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.execution import TestExecution
import pytest
from medperf import config
import yaml


PATCH_EXECUTION_FLOW = "medperf.commands.execution.execution_flow.{}"


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
        "execution": TestExecution(),
    }
    state_variables.update(request.param)

    # mocks/spies
    model_run_spy = mock_model(mocker, fs, state_variables)
    eval_run_spy = mock_eval(mocker, fs, state_variables)

    # mock update
    mocker.patch(
        PATCH_EXECUTION_FLOW.format("ExecutionFlow._ExecutionFlow__send_report")
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
        # Arrange
        execution = setup[0]["execution"]

        # Act & Assert
        with pytest.raises(ExecutionError):
            ExecutionFlow.run(
                INPUT_DATASET,
                INPUT_MODEL,
                INPUT_EVALUATOR,
                execution=execution,
                ignore_model_errors=False,
            )

    @pytest.mark.parametrize("setup", [{"failing_eval": True}], indirect=True)
    def test_failure_with_failing_eval_and_ignore_error(mocker, setup):
        # Arrange
        execution = setup[0]["execution"]

        # Act & Assert
        with pytest.raises(ExecutionError):
            ExecutionFlow.run(
                INPUT_DATASET,
                INPUT_MODEL,
                INPUT_EVALUATOR,
                execution=execution,
                ignore_model_errors=True,
            )

    @pytest.mark.parametrize("setup", [{"failing_model": True}], indirect=True)
    def test_no_failure_with_ignore_error(mocker, setup):
        # Arrange
        execution = setup[0]["execution"]

        # Act & Assert
        ExecutionFlow.run(
            INPUT_DATASET,
            INPUT_MODEL,
            INPUT_EVALUATOR,
            execution,
            ignore_model_errors=True,
        )


@pytest.mark.parametrize("setup", [{"failing_model": True}], indirect=True)
def test_partial_result_when_ignore_error_and_failing_model(mocker, setup):
    # Arrange
    execution = setup[0]["execution"]

    # Act
    execution_summary = ExecutionFlow.run(
        INPUT_DATASET,
        INPUT_MODEL,
        INPUT_EVALUATOR,
        execution=execution,
        ignore_model_errors=True,
    )

    # Assert
    assert execution_summary["partial"]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_no_partial_result_by_default(mocker, setup):
    # Arrange
    execution = setup[0]["execution"]

    # Act
    execution_summary = ExecutionFlow.run(
        INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, execution=execution
    )

    # Assert
    assert not execution_summary["partial"]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_results_are_returned(mocker, setup):
    # Arrange
    execution = setup[0]["execution"]

    # Act
    execution_summary = ExecutionFlow.run(
        INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, execution=execution
    )

    # Assert
    state_variables = setup[0]
    assert execution_summary["results"] == state_variables["execution_results"]


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_cube_run_are_called_properly(mocker, setup):
    # Arrange
    mocker.patch(PATCH_EXECUTION_FLOW.format("time"), return_value="tmp.uid")
    execution = setup[0]["execution"]
    exp_preds_path = os.path.join(
        config.predictions_folder, str(execution.id), "tmp_uid"
    )
    exp_local_outputs_path = os.path.join(execution.path, config.local_metrics_outputs)
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
            "local_outputs_path": exp_local_outputs_path,
        },
    )

    # Act
    ExecutionFlow.run(INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, execution=execution)

    # Assert
    spies = setup[1]
    spies["model_run"].assert_has_calls([exp_model_call])
    spies["eval_run"].assert_has_calls([exp_eval_call])
    spies["model_run"].assert_called_once()
    spies["eval_run"].assert_called_once()
