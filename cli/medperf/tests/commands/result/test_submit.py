import pytest

from medperf.tests.utils import rand_l
from medperf.entities import Result, Dataset
from medperf.commands.result import ResultSubmission

PATCH_SUBMISSION = "medperf.commands.result.submit.{}"


@pytest.fixture
def result(mocker):
    res = mocker.create_autospec(spec=Result)
    mocker.patch.object(res, "request_approval", return_value=True)
    return res


@pytest.fixture
def dataset(mocker):
    dset = mocker.create_autospec(spec=Dataset)
    dset.generated_uid = 1
    dset.uid = 1
    return dset


@pytest.fixture
def submission(mocker, comms, ui, result, dataset):
    sub = ResultSubmission(1, 1, 1, comms, ui)
    mocker.patch(PATCH_SUBMISSION.format("Result"), return_value=result)
    mocker.patch(PATCH_SUBMISSION.format("Dataset"), return_value=dataset)
    return sub


@pytest.mark.parametrize("bmark_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("data_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("model_uid", rand_l(1, 5000, 2))
def test_upload_results_looks_for_results_path(
    mocker, submission, bmark_uid, data_uid, model_uid
):
    # Arrange
    submission.benchmark_uid = bmark_uid
    submission.model_uid = model_uid
    submission.data_uid = data_uid
    spy = mocker.patch(PATCH_SUBMISSION.format("results_path"), return_value="")

    # Act
    submission.upload_results()

    # Assert
    spy.assert_called_once_with(bmark_uid, model_uid, data_uid)


def test_upload_results_requests_approval(mocker, submission, result):
    # Arrange
    spy = mocker.patch.object(result, "request_approval", return_value=True)

    # Act
    submission.upload_results()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("approved", [True, False])
def test_upload_results_fails_if_not_approved(mocker, submission, result, approved):
    # Arrange
    mocker.patch.object(result, "request_approval", return_value=approved)
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
def test_upload_results_uploads_if_approved(mocker, submission, result, approved):
    # Arrange
    mocker.patch.object(result, "request_approval", return_value=approved)
    spy = mocker.patch.object(result, "upload")
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
        spy.assert_called()
    else:
        spy.assert_not_called()


def test_run_executes_upload_procedure(mocker, comms, ui, submission):
    # Arrange
    bmark_uid = data_uid = model_uid = 1
    spy = mocker.spy(ResultSubmission, "upload_results")

    # Act
    ResultSubmission.run(bmark_uid, data_uid, model_uid, comms, ui)

    # Assert
    spy.assert_called_once()

