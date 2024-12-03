from medperf.exceptions import CleanExit
import pytest

from medperf.tests.mocks.execution import TestExecution
from medperf.tests.mocks.dataset import TestDataset

from medperf.commands.execution.submit import ResultSubmission
from medperf.enums import Status

PATCH_SUBMISSION = "medperf.commands.execution.submit.{}"


@pytest.fixture
def result():
    return TestExecution(id=None, approval_status=Status.PENDING)


@pytest.fixture
def dataset():
    return TestDataset(id=1)


@pytest.fixture
def submission(mocker, comms, ui, result, dataset):
    sub = ResultSubmission(1)
    mocker.patch(PATCH_SUBMISSION.format("Result"), return_value=result)
    mocker.patch(PATCH_SUBMISSION.format("Result.get"), return_value=result)
    sub.get_result()
    return sub


def test_upload_results_requests_approval(mocker, submission, result):
    # Arrange
    spy = mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=True)
    mocker.patch.object(result, "upload")
    mocker.patch.object(result, "write")
    mocker.patch("os.rename")
    # Act
    ResultSubmission.run(1)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("approved", [True, False])
def test_upload_results_fails_if_not_approved(mocker, submission, result, approved):
    # Arrange
    mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=approved)

    # Act & Assert
    if approved:
        submission.upload_results()
    else:
        with pytest.raises(CleanExit):
            submission.upload_results()


def test_run_executes_upload_procedure(mocker, comms, ui, submission):
    # Arrange
    result_uid = 1
    up_spy = mocker.spy(ResultSubmission, "upload_results")
    write_spy = mocker.spy(ResultSubmission, "write")
    mocker.patch.object(ui, "prompt", return_value="y")
    mocker.patch("os.rename")

    # Act
    ResultSubmission.run(result_uid)

    # Assert
    up_spy.assert_called_once()
    write_spy.assert_called_once()


def test_write_writes_results_using_entity(mocker, submission, result):
    # Arrange
    spy = mocker.patch.object(result, "write")

    # Act
    submission.write({})

    # Assert
    spy.assert_called()
