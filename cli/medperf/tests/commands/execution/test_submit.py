from medperf.exceptions import CleanExit
import pytest

from medperf.tests.mocks.execution import TestExecution
from medperf.tests.mocks.dataset import TestDataset

from medperf.commands.execution.submit import ResultSubmission

PATCH_SUBMISSION = "medperf.commands.execution.submit.{}"


@pytest.fixture
def result(fs):
    exec = TestExecution()
    exec.write()
    exec.save_results({}, False)
    exec.mark_as_executed()
    return exec


@pytest.fixture
def dataset():
    return TestDataset(id=1)


@pytest.fixture
def submission(mocker, comms, ui, result, dataset):
    mocker.patch(PATCH_SUBMISSION.format("Execution.all"), return_value=[result])
    mocker.patch(
        PATCH_SUBMISSION.format("get_medperf_user_data"), return_value={"id": 1}
    )
    mocker.patch(
        PATCH_SUBMISSION.format("filter_latest_executions"), side_effect=lambda x: x
    )
    sub = ResultSubmission(1, 1, 1)
    sub.get_execution()
    sub.prepare()
    return sub


def test_upload_results_requests_approval(mocker, submission, result):
    # Arrange
    spy = mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=True)
    mocker.patch(PATCH_SUBMISSION.format("ResultSubmission.write"))

    # Act
    ResultSubmission.run(1, 1, 1)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("approved", [True, False])
def test_upload_results_fails_if_not_approved(mocker, submission, result, approved):
    # Arrange
    mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=approved)

    # Act & Assert
    if approved:
        submission.update_execution()
    else:
        with pytest.raises(CleanExit):
            submission.update_execution()


def test_run_executes_upload_procedure(mocker, comms, ui, submission):
    # Arrange
    up_spy = mocker.spy(ResultSubmission, "update_execution")
    write_spy = mocker.patch(PATCH_SUBMISSION.format("ResultSubmission.write"))

    mocker.patch.object(ui, "prompt", return_value="y")

    # Act
    ResultSubmission.run(1, 1, 1)

    # Assert
    up_spy.assert_called_once()
    write_spy.assert_called_once()


def test_write_writes_results_using_entity(mocker, submission, result, fs):
    # Arrange
    spy = mocker.patch(PATCH_SUBMISSION.format("Execution.get"), return_value=result)

    # Act
    submission.write()

    # Assert
    spy.assert_called()
