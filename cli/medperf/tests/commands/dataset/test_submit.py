from medperf.tests.mocks.requests import dataset_dict
import pytest

from medperf.entities.dataset import Dataset
from medperf.commands.dataset.submit import DatasetRegistration

PATCH_REGISTER = "medperf.commands.dataset.submit.{}"


@pytest.fixture
def dataset(mocker):
    dset = mocker.create_autospec(spec=Dataset)
    mocker.patch(PATCH_REGISTER.format("Dataset.from_generated_uid"), return_value=dset)
    return dset


@pytest.fixture
def no_remote(mocker, comms):
    mocker.patch.object(comms, "get_user_datasets", return_value=[])


@pytest.mark.parametrize("data_uid", ["2214", "3540", "362"])
def test_run_retrieves_specified_dataset(
    mocker, comms, ui, dataset, data_uid, no_remote
):
    # Arrange
    dataset.uid = None
    mocker.patch(
        PATCH_REGISTER.format("approval_prompt"), return_value=True,
    )
    spy = mocker.patch(
        PATCH_REGISTER.format("Dataset.from_generated_uid"), return_value=dataset
    )

    # Act
    DatasetRegistration.run(data_uid, comms, ui)

    # Assert
    spy.assert_called_once_with(data_uid)


@pytest.mark.parametrize("uid", [3720, 1465, 4033])
def test_run_fails_if_dataset_already_registered(
    mocker, comms, ui, dataset, uid, no_remote
):
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


def test_run_passes_if_dataset_has_no_uid(mocker, comms, ui, dataset, no_remote):
    # Arrange
    dataset.uid = None
    mocker.patch(
        PATCH_REGISTER.format("approval_prompt"), return_value=True,
    )
    spy = mocker.patch(
        PATCH_REGISTER.format("pretty_error"),
        side_effect=lambda *args, **kwargs: exit(),
    )

    # Act
    DatasetRegistration.run("1", comms, ui)

    # Assert
    spy.assert_not_called()


def test_run_requests_approval(mocker, comms, ui, dataset, no_remote):
    # Arrange
    dataset.uid = None
    spy = mocker.patch(PATCH_REGISTER.format("approval_prompt"), return_value=True,)

    # Act
    DatasetRegistration.run("1", comms, ui)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("data_hash", ["data_hash", "data_hash_2"])
def test_updates_local_dset_if_remote_exists(mocker, comms, ui, dataset, data_hash):
    # Arrange
    dataset.uid = None
    dataset.generated_uid = data_hash
    remote_dsets = [
        dataset_dict(
            {
                "id": 1,
                "generated_uid": data_hash,
                "name": "name",
                "location": "location",
                "description": "description",
            }
        ),
        dataset_dict(
            {
                "id": 2,
                "generated_uid": "abc123",
                "name": "name",
                "location": "location",
                "description": "description",
            }
        ),
    ]
    mocker.patch.object(comms, "get_user_datasets", return_value=remote_dsets)
    write_spy = mocker.patch(PATCH_REGISTER.format("Dataset.write"))
    upload_spy = mocker.patch(PATCH_REGISTER.format("Dataset.upload"))

    # Act
    DatasetRegistration.run(data_hash, comms, ui)

    # Assert
    upload_spy.assert_not_called()
    write_spy.assert_called_once()


def test_fails_if_request_approval_rejected(mocker, comms, ui, dataset):
    # Arrange
    dataset.uid = None
    spy = mocker.patch(PATCH_REGISTER.format("approval_prompt"), return_value=False,)
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
        self, mocker, comms, ui, dataset, approved, no_remote
    ):
        # Arrange
        dataset.uid = None
        mocker.patch(
            PATCH_REGISTER.format("approval_prompt"), return_value=approved,
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

    def test_skips_request_approval_if_preapproved(
        self, mocker, comms, ui, dataset, approved
    ):
        # Arrange
        dataset.uid = None
        spy = mocker.patch(PATCH_REGISTER.format("approval_prompt"), return_value=True,)

        # Act
        DatasetRegistration.run("1", comms, ui, approved=approved)

        # Assert
        if approved:
            spy.assert_not_called()
