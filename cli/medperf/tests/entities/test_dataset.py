from medperf.enums import Status
import pytest
from unittest.mock import mock_open

import medperf
from medperf import utils
from medperf.ui.interface import UI
import medperf.config as config
from medperf.entities.dataset import Dataset

REGISTRATION_MOCK = {
    "name": "name",
    "description": "description",
    "location": "location",
    "data_preparation_mlcube": "data_preparation_mlcube",
    "split_seed": "split_seed",
    "metadata": {"metadata_key": "metadata_value"},
    "generated_uid": "generated_uid",
    "input_data_hash": "input_data_hash",
    "status": Status.PENDING.value,
    "uid": "uid",
    "state": "state",
}

PATCH_DATASET = "medperf.entities.dataset.{}"
TMP_PREFIX = config.tmp_prefix


@pytest.fixture
def ui(mocker):
    ui = mocker.create_autospec(spec=UI)
    return ui


@pytest.fixture
def basic_arrange(mocker):
    m = mock_open()
    mocker.patch("builtins.open", m, create=True)
    mocker.patch(PATCH_DATASET.format("yaml.safe_load"), return_value=REGISTRATION_MOCK)
    mocker.patch(PATCH_DATASET.format("os.path.exists"), return_value=True)
    return m


@pytest.fixture
def all_uids(mocker, basic_arrange, request):
    uids = request.param
    walk_out = iter([("", uids, [])])

    def mock_reg_file(ff):
        # Extract the uid of the opened registration file through the mocked object
        call_args = basic_arrange.call_args[0]
        # call args returns a tuple with the arguments called. Get the path
        path = call_args[0]
        # Get the uid by extracting second-to-last path element
        uid = path.split("/")[-2]
        # Assign the uid to the mocked registration dictionary
        reg = REGISTRATION_MOCK.copy()
        reg["generated_uid"] = uid
        return reg

    mocker.patch(PATCH_DATASET.format("yaml.safe_load"), side_effect=mock_reg_file)
    mocker.patch(PATCH_DATASET.format("os.walk"), return_value=walk_out)
    mocker.patch(PATCH_DATASET.format("get_uids"), return_value=uids)
    return uids


@pytest.mark.parametrize("all_uids", [[]], indirect=True)
def test_all_looks_for_dsets_in_data_storage(mocker, ui, all_uids):
    # Arrange
    walk_out = iter([("", [], [])])
    spy = mocker.patch(PATCH_DATASET.format("os.walk"), return_value=walk_out)

    # Act
    Dataset.all()

    # Assert
    spy.assert_called_once_with(utils.storage_path(config.data_storage))


def test_all_fails_if_cant_iterate_data_storage(mocker, ui):
    # Arrange
    walk_out = iter([])
    mocker.patch(PATCH_DATASET.format("os.walk"), return_value=walk_out)
    spy = mocker.patch(
        PATCH_DATASET.format("pretty_error"), side_effect=lambda *args, **kwargs: exit()
    )

    # Act
    with pytest.raises(SystemExit):
        Dataset.all()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("all_uids", [[], ["1", "2", "3"]], indirect=True)
def test_all_returns_list_of_expected_size(mocker, ui, all_uids):
    # Act
    dsets = Dataset.all()

    # Assert
    assert len(dsets) == len(all_uids)


@pytest.mark.parametrize("all_uids", [["1", "2", f"{TMP_PREFIX}3"]], indirect=True)
def test_all_ignores_temporary_datasets(mocker, ui, all_uids):
    # Act
    dsets = Dataset.all()
    uids = [dset.generated_uid for dset in dsets]

    # Assert
    assert f"{TMP_PREFIX}3" not in uids


@pytest.mark.parametrize("all_uids", [["1", "2", f"{TMP_PREFIX}3"]], indirect=True)
def test_dataset_metadata_is_backwards_compatible(mocker, ui, all_uids):
    # Arrange
    uid = "1"

    # Act
    dset = Dataset(uid)

    # Assert
    assert dset.generated_metadata == REGISTRATION_MOCK["metadata"]


@pytest.mark.parametrize(
    "all_uids", [["2", "3"], ["1", "12"], ["12", "1"]], indirect=True
)
def test_full_uid_fails_when_single_match_not_found(mocker, ui, all_uids):
    # Arrange
    spy = mocker.patch(PATCH_DATASET.format("pretty_error"))

    # Act
    uid = "1"
    Dataset(uid)

    # Arrange
    spy.assert_called_once()


@pytest.mark.parametrize("all_uids", [["12", "3"], ["3", "5", "12"]], indirect=True)
def test_full_uid_finds_expected_match(mocker, ui, all_uids):
    # Act
    uid = "1"
    dset = Dataset(uid)

    # Assert
    assert dset.generated_uid == "12"


@pytest.mark.parametrize("all_uids", [["1"]], indirect=True)
def test_get_registration_looks_for_registration_file(mocker, ui, all_uids):
    # Arrange
    uid = "1"
    dset = Dataset(uid)
    spy = mocker.spy(medperf.entities.dataset.os.path, "join")

    # Act
    dset.get_registration()

    # Assert
    spy.assert_called_once_with(dset.dataset_path, config.reg_file)


@pytest.mark.parametrize("all_uids", [["1"]], indirect=True)
def test_get_registration_loads_yaml_file(mocker, ui, all_uids):
    # Arrange
    uid = "1"
    dset = Dataset(uid)
    spy = mocker.spy(medperf.entities.dataset.yaml, "safe_load")

    # Act
    dset.get_registration()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("all_uids", [["1"]], indirect=True)
@pytest.mark.parametrize("comms_uid", [1, 4, 834, 12])
def test_upload_returns_uid_from_comms(mocker, all_uids, ui, comms_uid, comms):
    # Arrange
    uid = "1"
    mocker.patch.object(comms, "upload_dataset", return_value=comms_uid)
    dset = Dataset(uid)

    # Act
    uid = dset.upload(comms)

    # Assert
    assert uid == comms_uid
