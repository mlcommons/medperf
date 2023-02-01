from medperf.exceptions import CleanExit
import pytest

from medperf.entities.result import Result
from medperf.entities.dataset import Dataset
from medperf.commands.result.submit import ResultSubmission
from medperf.enums import Status

PATCH_SUBMISSION = "medperf.commands.result.submit.{}"


@pytest.fixture
def result(mocker):
    res = mocker.create_autospec(spec=Result)
    res.status = Status.PENDING
    res.generated_uid = "generated_uid"
    res.path = "path"
    res.results = {}
    return res


@pytest.fixture
def dataset(mocker):
    dset = mocker.create_autospec(spec=Dataset)
    dset.generated_uid = 1
    dset.uid = 1
    return dset


@pytest.fixture
def submission(mocker, comms, ui, result, dataset):
    sub = ResultSubmission(1)
    mocker.patch(PATCH_SUBMISSION.format("Result"), return_value=result)
    mocker.patch(PATCH_SUBMISSION.format("Result.get"), return_value=result)
    mocker.patch("medperf.entities.result.Dataset.get", return_vlaue=dataset)
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
