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
    sub = ResultSubmission(1, 1, 1)
    mocker.patch(PATCH_SUBMISSION.format("Result"), return_value=result)
    mocker.patch(PATCH_SUBMISSION.format("Result.get"), return_value=result)
    mocker.patch(PATCH_SUBMISSION.format("Dataset"), return_value=dataset)
    return sub


def test_upload_results_requests_approval(mocker, submission, result):
    # Arrange
    spy = mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=True)

    # Act
    submission.upload_results()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("approved", [True, False])
def test_upload_results_fails_if_not_approved(mocker, submission, result, approved):
    # Arrange
    mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=approved)
    spy = mocker.patch(
        PATCH_SUBMISSION.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    try:
        submission.upload_results()
    except SystemExit:
        pass

    # Assert
    if approved:
        spy.assert_not_called()
    else:
        spy.assert_called()


@pytest.mark.parametrize("approved", [True, False])
def test_upload_results_uploads_if_approved(mocker, result, submission, approved):
    # Arrange
    mocker.patch(PATCH_SUBMISSION.format("approval_prompt"), return_value=approved)
    mocker.patch(
        PATCH_SUBMISSION.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    try:
        submission.upload_results()
    except SystemExit:
        pass

    # Assert
    if approved:
        result.upload.assert_called()
    else:
        result.upload.assert_not_called()


def test_run_executes_upload_procedure(mocker, comms, ui, submission):
    # Arrange
    bmark_uid = data_uid = model_uid = 1
    up_spy = mocker.spy(ResultSubmission, "upload_results")
    write_spy = mocker.spy(ResultSubmission, "write")
    mocker.patch.object(ui, "prompt", return_value="y")
    mocker.patch("os.rename")

    # Act
    ResultSubmission.run(bmark_uid, data_uid, model_uid)

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
