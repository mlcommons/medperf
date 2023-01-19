from medperf.exceptions import CleanExit, InvalidArgumentError
from medperf.tests.mocks.requests import dataset_dict
import pytest

from medperf.tests.mocks.dataset import TestDataset
from medperf.commands.dataset.submit import DatasetRegistration

PATCH_REGISTER = "medperf.commands.dataset.submit.{}"


@pytest.fixture
def dataset(mocker):
    dset = TestDataset(id=None, generated_uid="generated_uid")
    mocker.patch(PATCH_REGISTER.format("Dataset.get"), return_value=dset)
    mocker.patch(PATCH_REGISTER.format("Dataset.upload"), return_value=dset.todict())
    return dset


@pytest.fixture
def no_remote(mocker, comms):
    mocker.patch.object(comms, "get_user_datasets", return_value=[])


@pytest.mark.parametrize("data_uid", ["2214", "3540", "362"])
def test_run_retrieves_specified_dataset(
    mocker, comms, ui, dataset, data_uid, no_remote
):
    # Arrange
    mocker.patch(
        PATCH_REGISTER.format("approval_prompt"), return_value=True,
    )
    spy = mocker.patch(PATCH_REGISTER.format("Dataset.get"), return_value=dataset)
    mocker.patch(PATCH_REGISTER.format("Dataset.write"))
    mocker.patch("os.rename")

    # Act
    DatasetRegistration.run(data_uid)

    # Assert
    spy.assert_called_once_with(data_uid)


@pytest.mark.parametrize("uid", [3720, 1465, 4033])
def test_run_fails_if_dataset_already_registered(
    mocker, comms, ui, dataset, uid, no_remote
):
    # Arrange
    dataset.id = uid

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        DatasetRegistration.run("1")


def test_run_passes_if_dataset_has_no_uid(mocker, comms, ui, dataset, no_remote):
    # Arrange
    mocker.patch(
        PATCH_REGISTER.format("approval_prompt"), return_value=True,
    )
    mocker.patch(PATCH_REGISTER.format("Dataset.write"))
    mocker.patch("os.rename")

    # Act & Assert
    DatasetRegistration.run("1")


@pytest.mark.parametrize("dset_dict", [{"test": "test"}, {}])
def test_run_prints_dset_dict(mocker, comms, ui, dataset, no_remote, dset_dict):
    # Arrange
    spy_dict = mocker.patch.object(dataset, "todict", return_value=dset_dict)
    spy = mocker.patch(PATCH_REGISTER.format("dict_pretty_print"))
    mocker.patch(
        PATCH_REGISTER.format("approval_prompt"), return_value=True,
    )
    mocker.patch(PATCH_REGISTER.format("Dataset.write"))
    mocker.patch("os.rename")

    # Act
    DatasetRegistration.run("1")

    # Assert
    spy_dict.assert_called_once()
    spy.assert_called_once_with(dset_dict)


def test_run_requests_approval(mocker, comms, ui, dataset, no_remote):
    # Arrange
    spy = mocker.patch(PATCH_REGISTER.format("approval_prompt"), return_value=True,)
    mocker.patch(PATCH_REGISTER.format("Dataset.write"))
    mocker.patch("os.rename")

    # Act
    DatasetRegistration.run("1")

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("data_hash", ["data_hash", "data_hash_2"])
def test_updates_local_dset_if_remote_exists(mocker, comms, ui, dataset, data_hash):
    # Arrange
    dataset.generated_uid = data_hash
    remote_dsets_dicts = [{"id": 1, "generated_uid": data_hash}]
    remote_dsets = [
        TestDataset(**dset_dict).todict() for dset_dict in remote_dsets_dicts
    ]
    mocker.patch.object(comms, "get_user_datasets", return_value=remote_dsets)
    write_spy = mocker.patch(PATCH_REGISTER.format("Dataset.write"))
    upload_spy = mocker.patch(
        PATCH_REGISTER.format("Dataset.upload"), return_value=dataset.todict()
    )

    # Act
    DatasetRegistration.run(data_hash)

    # Assert
    upload_spy.assert_not_called()
    write_spy.assert_called_once()


@pytest.mark.parametrize("approved", [True, False])
class TestWithApproval:
    def test_run_uploads_dataset_if_approved(
        self, mocker, comms, ui, dataset, approved, no_remote
    ):
        # Arrange
        mocker.patch(
            PATCH_REGISTER.format("approval_prompt"), return_value=approved,
        )
        spy = mocker.patch.object(dataset, "upload", return_value=dataset.todict())
        mocker.patch(PATCH_REGISTER.format("Dataset.write"))
        mocker.patch("os.rename")

        # Act
        if approved:
            DatasetRegistration.run("1")
        else:
            with pytest.raises(CleanExit):
                DatasetRegistration.run("1")

        # Assert
        if approved:
            spy.assert_called_once()
        else:
            spy.assert_not_called()

    def test_skips_request_approval_if_preapproved(
        self, mocker, comms, ui, dataset, approved
    ):
        # Arrange
        spy = mocker.patch(PATCH_REGISTER.format("approval_prompt"), return_value=True,)
        mocker.patch(PATCH_REGISTER.format("Dataset.write"))
        mocker.patch("os.rename")

        # Act
        DatasetRegistration.run("1", approved=approved)

        # Assert
        if approved:
            spy.assert_not_called()
        else:
            spy.assert_called_once()

    def test_run_writes_dataset_if_uploads(
        self, mocker, comms, ui, dataset, approved, no_remote
    ):
        # Arrange
        mocker.patch(
            PATCH_REGISTER.format("approval_prompt"), return_value=approved,
        )
        mocker.patch.object(dataset, "upload", return_value=dataset.todict())
        spy = mocker.patch(PATCH_REGISTER.format("Dataset.write"))
        mocker.patch("os.rename")

        # Act
        if approved:
            DatasetRegistration.run("1")
        else:
            with pytest.raises(CleanExit):
                DatasetRegistration.run("1")

        # Assert
        if approved:
            spy.assert_called_once()
        else:
            spy.assert_not_called()
