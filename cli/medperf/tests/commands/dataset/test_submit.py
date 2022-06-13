import pytest

from medperf.tests.utils import rand_l
from medperf.entities.dataset import Dataset
from medperf.commands.dataset.submit import DatasetRegistration

PATCH_REGISTER = "medperf.commands.dataset.submit.{}"


@pytest.fixture
def dataset(mocker):
    dset = mocker.create_autospec(spec=Dataset)
    mocker.patch(PATCH_REGISTER.format("Dataset"), return_value=dset)
    return dset


@pytest.mark.parametrize("data_uid", [str(x) for x in rand_l(1, 5000, 5)])
def test_run_retrieves_specified_dataset(mocker, comms, ui, dataset, data_uid):
    # Arrange
    dataset.uid = None
    spy = mocker.patch(PATCH_REGISTER.format("Dataset"), return_value=dataset)

    # Act
    DatasetRegistration.run(data_uid, comms, ui)

    # Assert
    spy.assert_called_once_with(data_uid, ui)


@pytest.mark.parametrize("uid", rand_l(1, 5000, 5))
def test_run_fails_if_dataset_already_registered(mocker, comms, ui, dataset, uid):
    # Arrange
    dataset.uid = uid
    spy = mocker.patch(
        PATCH_REGISTER.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    with pytest.raises(SystemExit):
        DatasetRegistration.run("1", comms, ui)

    # Assert
    spy.assert_called_once()


def test_run_passes_if_dataset_has_no_uid(mocker, comms, ui, dataset):
    # Arrange
    dataset.uid = None
    spy = mocker.patch(
        PATCH_REGISTER.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    DatasetRegistration.run("1", comms, ui)

    # Assert
    spy.assert_not_called()


def test_run_requests_approval(mocker, comms, ui, dataset):
    # Arrange
    dataset.uid = None
    spy = mocker.patch.object(
        dataset, "request_registration_approval", return_value=True
    )

    # Act
    DatasetRegistration.run("1", comms, ui)

    # Assert
    spy.assert_called_once()


def test_fails_if_request_approval_rejected(mocker, comms, ui, dataset):
    # Arrange
    dataset.uid = None
    spy = mocker.patch.object(
        dataset, "request_registration_approval", return_value=False
    )
    mocker.patch(
        PATCH_REGISTER.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    with pytest.raises(SystemExit):
        DatasetRegistration.run("1", comms, ui)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("approved", [True, False])
class TestWithApproval:
    def test_run_uploads_dataset_if_approved(
        self, mocker, comms, ui, dataset, approved
    ):
        # Arrange
        dataset.uid = None
        mocker.patch.object(
            dataset, "request_registration_approval", return_value=approved
        )
        spy = mocker.patch.object(dataset, "upload")
        mocker.patch(PATCH_REGISTER.format("pretty_error"))

        # Act
        DatasetRegistration.run("1", comms, ui)

        # Assert
        if approved:
            spy.assert_called_once()
        else:
            spy.assert_not_called()

    def test_run_updates_registration_if_approved(
        self, mocker, comms, ui, dataset, approved
    ):
        # Arrange
        dataset.uid = None
        mocker.patch.object(
            dataset, "request_registration_approval", return_value=approved
        )
        spy = mocker.patch.object(dataset, "set_registration")
        mocker.patch(PATCH_REGISTER.format("pretty_error"))

        # Act
        DatasetRegistration.run("1", comms, ui)

        # Assert
        if approved:
            spy.assert_called_once()
        else:
            spy.assert_not_called()

    def test_skips_request_approval_if_preapproved(
        self, mocker, comms, ui, dataset, approved
    ):
        # Arrange
        dataset.uid = None
        spy = mocker.patch.object(
            dataset, "request_registration_approval", return_value=True,
        )

        # Act
        DatasetRegistration.run("1", comms, ui, approved=approved)

        # Assert
        if approved:
            spy.assert_not_called()
