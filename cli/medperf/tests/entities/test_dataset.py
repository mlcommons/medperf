import pytest
from unittest.mock import MagicMock

import medperf
from medperf.config import config
from medperf.entities import Dataset
from medperf.ui import UI
from medperf.tests.mocks import Benchmark

registration_mock = {
    "name": "name",
    "description": "description",
    "location": "location",
    "data_preparation_mlcube": "data_preparation_mlcube",
    "split_seed": "split_seed",
    "metadata": {},
    "generated_uid": "generated_uid",
    "status": "status",
}

patch_dataset = "medperf.entities.dataset.{}"
tmp_prefix = config["tmp_reg_prefix"]


@pytest.fixture
def ui(mocker):
    ui = mocker.create_autospec(spec=UI)
    return ui


@pytest.fixture
def basic_arrange(mocker):
    mocker.patch("builtins.open", MagicMock())
    mocker.patch(patch_dataset.format("yaml.full_load"), return_value=registration_mock)
    mocker.patch(patch_dataset.format("os.path.exists"), return_value=True)


@pytest.fixture
def all_uids(mocker, basic_arrange, request):
    uids = request.param
    walk_out = iter([("", uids, [])])
    mocker.patch(patch_dataset.format("os.walk"), return_value=walk_out)
    mocker.patch(patch_dataset.format("get_dsets"), return_value=uids)
    return uids


@pytest.mark.parametrize("all_uids", [[]], indirect=True)
def test_all_looks_for_dsets_in_data_storage(mocker, ui, all_uids):
    walk_out = iter([("", [], [])])
    spy = mocker.patch(patch_dataset.format("os.walk"), return_value=walk_out)

    # Act
    Dataset.all(ui)

    # Assert
    spy.assert_called_once_with(config["data_storage"])


@pytest.mark.parametrize("all_uids", [[], ["1", "2", "3"]], indirect=True)
def test_all_returns_list_of_expected_size(mocker, ui, all_uids):
    # Act
    dsets = Dataset.all(ui)

    # Assert
    assert len(dsets) == len(all_uids)


@pytest.mark.parametrize("all_uids", [["1", "2", f"{tmp_prefix}3"]], indirect=True)
def test_all_ignores_temporary_datasets(mocker, ui, all_uids):
    # Act
    dsets = Dataset.all(ui)
    uids = [dset.data_uid for dset in dsets]

    # Assert
    assert f"{tmp_prefix}3" not in uids


@pytest.mark.parametrize(
    "all_uids", [["2", "3"], ["1", "12"], ["12", "1"]], indirect=True
)
def test_full_uid_fails_when_single_match_not_found(mocker, ui, all_uids):
    # Arrange
    spy = mocker.patch(patch_dataset.format("pretty_error"))

    # Act
    uid = "1"
    Dataset(uid, ui)

    # Arrange
    spy.assert_called_once()


@pytest.mark.parametrize("all_uids", [["12", "3"], ["3", "5", "12"]], indirect=True)
def test_full_uid_finds_expected_match(mocker, ui, all_uids):
    # Act
    uid = "1"
    dset = Dataset(uid, ui)

    # Assert
    assert dset.data_uid == "12"


@pytest.mark.parametrize("all_uids", [["1"]], indirect=True)
def test_get_registration_looks_for_registration_file(mocker, ui, all_uids):
    # Arrange
    uid = "1"
    dset = Dataset(uid, ui)
    spy = mocker.spy(medperf.entities.dataset.os.path, "join")

    # Act
    dset.get_registration()

    # Assert
    spy.assert_called_once_with(dset.dataset_path, config["reg_file"])


@pytest.mark.parametrize("all_uids", [["1"]], indirect=True)
def test_get_registration_loads_yaml_file(mocker, ui, all_uids):
    # Arrange
    uid = "1"
    dset = Dataset(uid, ui)
    spy = mocker.spy(medperf.entities.dataset.yaml, "full_load")

    # Act
    dset.get_registration()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("all_uids", [["1"]], indirect=True)
def test_association_approval_skips_when_already_approved(mocker, ui, all_uids):
    # Arrange
    uid = "1"
    dset = Dataset(uid, ui)
    dset.status = "APPROVED"
    mock_benchmark = Benchmark()
    spy = mocker.patch(patch_dataset.format("approval_prompt"), return_value=True)

    # Act
    dset.request_association_approval(mock_benchmark, ui)

    # Assert
    spy.assert_not_called()


@pytest.mark.parametrize("all_uids", [["1"]], indirect=True)
def test_association_approval_prompts_user(mocker, ui, all_uids):
    # Arrange
    uid = "1"
    dset = Dataset(uid, ui)
    mock_benchmark = Benchmark()
    spy = mocker.patch(patch_dataset.format("approval_prompt"), return_value=True)

    # Act
    dset.request_association_approval(mock_benchmark, ui)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("all_uids", [["1"]], indirect=True)
@pytest.mark.parametrize("exp_return", [True, False])
def test_association_approval_returns_prompt_value(mocker, ui, all_uids, exp_return):
    # Arrange
    uid = "1"
    dset = Dataset(uid, ui)
    mock_benchmark = Benchmark()
    mocker.patch(patch_dataset.format("approval_prompt"), return_value=exp_return)

    # Act
    approved = dset.request_association_approval(mock_benchmark, ui)

    # Assert
    assert approved == exp_return
