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
    mocker.patch(PATCH_SUBMISSION.format("Result"), return_value=result)
    mocker.patch(
        PATCH_SUBMISSION.format("Result.from_entities_uids"), return_value=result
    )
    mocker.patch(
        PATCH_SUBMISSION.format("Dataset.from_generated_uid"), return_value=dataset
    )
    mocker.patch(PATCH_SUBMISSION.format("dict_pretty_print"))


def test_upload_results_requests_approval(mocker, submission, result):
    # Arrange
    spy = mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=True)
    mocker.patch.object(result, "upload")
    mocker.patch.object(result, "write")
    # Act
    ResultSubmission.run(1, 1, 1)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("approved", [True, False])
def test_upload_results_fails_if_not_approved(mocker, submission, result, approved):
    # Arrange
    mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=approved)
    upload_spy = mocker.patch.object(result, "upload")
    write_spy = mocker.patch.object(result, "write")

    # Act
    ResultSubmission.run(1, 1, 1)

    # Assert
    if approved:
        upload_spy.assert_called()
        write_spy.assert_called()
    else:
        upload_spy.assert_not_called()
        write_spy.assert_not_called()
