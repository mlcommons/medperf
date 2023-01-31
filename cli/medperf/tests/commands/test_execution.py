from medperf.commands.execution import Execution
from medperf.exceptions import ExecutionError
from medperf.tests.mocks.cube import generate_cube
from medperf.tests.mocks.dataset import generate_dset
import pytest

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
import yaml


PATCH_EXECUTION = "medperf.commands.execution.{}"


INPUT_DATASET = Dataset(generate_dset())
INPUT_MODEL = Cube(generate_cube(id=2))
INPUT_EVALUATOR = Cube(generate_cube(id=3))


def mock_model(mocker, system_inputs):
    failing_model = system_inputs["failing_model"]

    def _side_effect(*args, **kwargs):
        if failing_model:
            raise ExecutionError

    spy = mocker.patch.object(INPUT_MODEL, "run", side_effect=_side_effect)
    return spy


def mock_eval(mocker, fs, system_inputs):
    failing_eval = system_inputs["failing_eval"]
    execution_results = system_inputs["execution_results"]

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
    system_inputs = {
        "failing_model": False,
        "failing_eval": False,
        "execution_results": {"res": 1, "metric": 55},
    }
    system_inputs.update(request.param)

    # mocks/spies
    model_run_spy = mock_model(mocker, system_inputs)
    eval_run_spy = mock_eval(mocker, fs, system_inputs)
    cleanup_spy = mocker.patch(PATCH_EXECUTION.format("cleanup_path"))

    spies = {
        "model_run": model_run_spy,
        "eval_run": eval_run_spy,
        "cleanup": cleanup_spy,
    }
    return system_inputs, spies


class TestFailures:
    @pytest.mark.parametrize(
        "setup", [{"failing_model": True}, {"failing_eval": True}], indirect=True
    )
    def test_failure_with_failing_cubes_and_no_ignore_error(mocker, setup):
        # Act & Assert
        with pytest.raises(ExecutionError):
            Execution.run(
                INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, ignore_errors=False
            )
        spies = setup[1]
        spies["cleanup"].assert_called_once()

    @pytest.mark.parametrize("setup", [{"failing_eval": True}], indirect=True)
    def test_failure_with_failing_eval_and_ignore_error(mocker, setup):
        # Act & Assert
        with pytest.raises(ExecutionError):
            Execution.run(
                INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, ignore_errors=True
            )
        spies = setup[1]
        spies["cleanup"].assert_called_once()

    @pytest.mark.parametrize("setup", [{"failing_model": True}], indirect=True)
    def test_no_failure_with_ignore_error(mocker, setup):
        # Act
        Execution.run(INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, ignore_errors=True)

        # Assert
        spies = setup[1]
        spies["cleanup"].assert_not_called()


@pytest.mark.parametrize("setup", [{"failing_model": True}], indirect=True)
def test_partial_result_when_ignore_error_and_failing_model(mocker, setup):
    # Act
    execution_summary = Execution.run(
        INPUT_DATASET, INPUT_MODEL, INPUT_EVALUATOR, ignore_errors=True
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
    system_inputs = setup[0]
    assert execution_summary["results"] == system_inputs["execution_results"]
