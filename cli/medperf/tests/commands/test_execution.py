import os
from unittest.mock import ANY, call
from medperf.commands.execution import Execution
from medperf.exceptions import ExecutionError
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.utils import storage_path
import pytest
from medperf import config
import yaml


PATCH_EXECUTION = "medperf.commands.execution.{}"


INPUT_DATASET = TestDataset()
INPUT_MODEL = TestCube(id=2)
INPUT_EVALUATOR = TestCube(id=3)


def mock_model(mocker, state_variables):
    failing_model = state_variables["failing_model"]

    def _side_effect(*args, **kwargs):
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
        out_path = kwargs["output_path"]
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
    }
    state_variables.update(request.param)

    # mocks/spies
    model_run_spy = mock_model(mocker, state_variables)
    eval_run_spy = mock_eval(mocker, fs, state_variables)

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
    preds_path = os.path.join(
        storage_path(config.predictions_storage),
        str(INPUT_MODEL.id),
        str(INPUT_DATASET.generated_uid),
    )
    exp_model_call = call(
        task="infer",
        timeout=config.infer_timeout,
        data_path=INPUT_DATASET.data_path,
        output_path=preds_path,
        string_params={"Ptasks.infer.parameters.input.data_path.opts": "ro"},
    )
    exp_eval_call = call(
        task="evaluate",
        timeout=config.evaluate_timeout,
        predictions=preds_path,
        labels=INPUT_DATASET.labels_path,
        output_path=ANY,
        string_params={
            "Ptasks.evaluate.parameters.input.predictions.opts": "ro",
            "Ptasks.evaluate.parameters.input.labels.opts": "ro",
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
