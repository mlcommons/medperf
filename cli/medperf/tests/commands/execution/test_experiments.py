import os

import pytest

from medperf import config
from medperf.commands.execution.experiments import Experiment, ExperimentsRunner
from medperf.commands.execution.plan import BenchmarkPlan
from medperf.enums import BenchmarkTopology
from medperf.exceptions import ExecutionError, InvalidEntityError
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.execution import TestExecution
from medperf.tests.mocks.model import TestContainerModel

PATCH_RUNNER = "medperf.commands.execution.experiments.{}"

BENCHMARK_UID = 1
DATA_UID = 2
OWNER = 1

PLAN = BenchmarkPlan(
    topology=BenchmarkTopology.BYO_INFERENCE_SCRIPT,
    benchmark_id=BENCHMARK_UID,
    evaluator=TestCube(id=3),
)


def experiment(model_uid, data_uid=DATA_UID):
    return Experiment(
        dataset=TestDataset(id=data_uid), model=TestContainerModel(id=model_uid)
    )


def mock_executions(mocker, fs, state_variables):
    """The Execution entity, as this module sees it.

    Creating one hands back a `TestExecution`; listing them hands back the ones
    this user already has for this benchmark. Each entry of `existing` is
    (execution_id, model_uid, executed, finalized)."""
    executions = []
    for exec_id, model_uid, executed, finalized in state_variables["existing"]:
        execution = TestExecution(
            id=exec_id,
            benchmark=BENCHMARK_UID,
            model=model_uid,
            dataset=DATA_UID,
            owner=OWNER,
            finalized=finalized,
            created_at="2026-01-01T00:00:00Z",
        )
        if executed:
            fs.create_file(os.path.join(execution.path, config.executed_flag))
        executions.append(execution)

    mocker.patch(
        PATCH_RUNNER.format("get_medperf_user_data"), return_value={"id": OWNER}
    )
    execution_cls = mocker.patch(
        PATCH_RUNNER.format("Execution"), side_effect=TestExecution
    )
    execution_cls.all.return_value = executions
    return execution_cls


def mock_execution_flow(mocker, state_variables):
    def __run(plan, dataset, model, execution, ignore_model_errors):
        outcome = state_variables["outcomes"].get(model.id, {})
        if outcome == "exec_error":
            raise ExecutionError("model blew up")
        if outcome == "invalid_entity":
            raise InvalidEntityError("model container is invalid")
        return {"results": {"score": model.id}, "partial": False, **outcome}

    return mocker.patch(PATCH_RUNNER.format("ExecutionFlow.run"), side_effect=__run)


@pytest.fixture()
def setup(request, mocker, ui, fs):
    state_variables = {
        "existing": [],
        "outcomes": {},
    }
    state_variables.update(request.param)

    created_spy = mock_executions(mocker, fs, state_variables)
    flow_spy = mock_execution_flow(mocker, state_variables)
    save_spy = mocker.patch.object(TestExecution, "save_results")

    spies = {"flow": flow_spy, "created": created_spy, "save": save_spy}
    return state_variables, spies


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_a_pair_with_no_execution_yet_is_run(setup):
    # Arrange
    _, spies = setup

    # Act
    ExperimentsRunner.run(BENCHMARK_UID, PLAN, [experiment(4)])

    # Assert
    spies["flow"].assert_called_once()
    spies["save"].assert_called_once_with({"score": 4}, False, {})


@pytest.mark.parametrize(
    "setup", [{"existing": [(10, 4, True, False)]}], indirect=True
)
def test_an_already_executed_pair_is_taken_from_the_cache(setup):
    # Arrange
    _, spies = setup

    # Act
    executions = ExperimentsRunner.run(BENCHMARK_UID, PLAN, [experiment(4)])

    # Assert
    spies["flow"].assert_not_called()
    assert [execution.id for execution in executions] == [10]


@pytest.mark.parametrize(
    "setup", [{"existing": [(10, 4, True, False)]}], indirect=True
)
def test_no_cache_reruns_an_execution_that_was_not_reported(setup):
    # Arrange
    _, spies = setup

    # Act
    ExperimentsRunner.run(BENCHMARK_UID, PLAN, [experiment(4)], no_cache=True)

    # Assert
    spies["flow"].assert_called_once()


@pytest.mark.parametrize("setup", [{"existing": [(10, 4, True, True)]}], indirect=True)
def test_no_cache_leaves_a_reported_execution_alone(setup):
    """Its results are on the server already -- overwriting them locally would
    say nothing to anybody"""
    # Arrange
    _, spies = setup

    # Act
    ExperimentsRunner.run(BENCHMARK_UID, PLAN, [experiment(4)], no_cache=True)

    # Assert
    spies["flow"].assert_not_called()


@pytest.mark.parametrize("setup", [{"existing": [(10, 4, True, True)]}], indirect=True)
def test_rerunning_a_reported_execution_creates_a_new_record(setup):
    """The reported one stays as it is; this is a second run, not an edit"""
    # Arrange
    _, spies = setup

    # Act
    ExperimentsRunner.run(
        BENCHMARK_UID, PLAN, [experiment(4)], rerun_finalized_executions=True
    )

    # Assert
    spies["created"].assert_called()
    spies["flow"].assert_called_once()


@pytest.mark.parametrize(
    "setup", [{"outcomes": {4: "exec_error"}}], indirect=True
)
def test_a_failing_experiment_is_raised_by_default(setup):
    # Act & Assert
    with pytest.raises(ExecutionError):
        ExperimentsRunner.run(BENCHMARK_UID, PLAN, [experiment(4)])


@pytest.mark.parametrize(
    "setup", [{"outcomes": {4: "exec_error"}}], indirect=True
)
def test_a_failing_experiment_can_be_ignored(setup):
    # Arrange
    _, spies = setup

    # Act
    executions = ExperimentsRunner.run(
        BENCHMARK_UID,
        PLAN,
        [experiment(4), experiment(5)],
        ignore_failed_experiments=True,
    )

    # Assert -- the failed one reports no execution, the next one still runs
    assert executions[0] is None
    assert executions[1] is not None


@pytest.mark.parametrize(
    "setup", [{"outcomes": {4: "invalid_entity"}}], indirect=True
)
def test_an_invalid_model_container_is_reported_against_its_model(setup, ui):
    # Act
    ExperimentsRunner.run(
        BENCHMARK_UID, PLAN, [experiment(4)], ignore_failed_experiments=True
    )

    # Assert
    printed = " ".join(str(call) for call in ui.print_error.call_args_list)
    assert "model container 4" in printed


@pytest.mark.parametrize("setup", [{}], indirect=True)
def test_the_summary_names_both_sides_of_every_pair(setup, ui):
    """The same table serves a data owner running many models and a model
    owner running many datasets, so neither side is left implicit"""
    # Act
    ExperimentsRunner.run(
        BENCHMARK_UID, PLAN, [experiment(4), experiment(5)], show_summary=True
    )

    # Assert
    printed = "\n".join(str(call) for call in ui.print.call_args_list)
    assert "model" in printed and "dataset" in printed
    assert "Total number of experiments: 2" in printed
