import medperf
from medperf.entities import Registration, Cube, Server

from unittest.mock import MagicMock
import os
from pathlib import Path
import pytest

OUT_PATH = "out_path"
PATCH_REGISTRATION = "medperf.entities.registration.{}"
PATCH_CUBE = "medperf.entities.cube.{}"
REG_DICT_KEYS = [
    "name",
    "description",
    "location",
    "split_seed",
    "data_preparation_mlcube",
    "generated_uid",
    "input_data_hash",
    "metadata",
    "status",
]


class MockedDataset:
    def __init__(self, uid):
        self.registration = {"generated_uid": uid}


@pytest.fixture
def reg_init_params():
    cube = Cube(1, {"name": ""}, "")
    name = "mock registration"
    description = "mock_description"
    location = "mock location"
    return [cube, name, description, location]


@pytest.fixture
def reg_mocked_with_params(mocker, reg_init_params):
    mocker.patch(
        PATCH_REGISTRATION.format("Registration._Registration__get_stats"),
        return_value={},
    )
    return reg_init_params


@pytest.mark.parametrize("mock_hash", ["hash1", "hash2", "hash3"])
def test_generate_uid_returns_folder_hash(mocker, mock_hash, reg_init_params):
    # Arrange
    mocker.patch(PATCH_REGISTRATION.format("get_folder_sha1"), return_value=mock_hash)
    mocker.patch(
        PATCH_REGISTRATION.format("Registration._Registration__get_stats"),
        return_value={},
    )

    # Act
    registration = Registration(*reg_init_params)
    gen_hash = registration.generate_uid(OUT_PATH)

    # Assert
    assert gen_hash == mock_hash


@pytest.mark.parametrize("path", ["stats_path", "./workspace/outputs/statistics.yaml"])
def test_get_stats_opens_stats_path(mocker, path, reg_init_params):
    # Arrange
    spy = mocker.patch("builtins.open", MagicMock())
    mocker.patch(PATCH_CUBE.format("Cube.get_default_output"), return_value=path)
    mocker.patch(PATCH_REGISTRATION.format("yaml.full_load"), return_value={})

    # Act
    Registration(*reg_init_params)

    # Assert
    spy.assert_called_once_with(path, "r")


@pytest.mark.parametrize("stats", [{}, {"test": ""}, {"mean": 8}])
def test_get_stats_returns_stats(mocker, stats, reg_init_params):
    # Arrange
    mocker.patch("builtins.open", MagicMock())
    mocker.patch(PATCH_CUBE.format("Cube.get_default_output"), return_value="")
    mocker.patch(PATCH_REGISTRATION.format("yaml.full_load"), return_value=stats)

    # Act
    registration = Registration(*reg_init_params)

    # Assert
    assert registration.stats == stats


def test_todict_returns_expected_keys(mocker, reg_mocked_with_params):
    # Act
    registration = Registration(*reg_mocked_with_params)

    # Assert
    assert set(registration.todict().keys()) == set(REG_DICT_KEYS)


@pytest.mark.parametrize(
    "inputs", [["name", "desc", "loc"], ["chex", "chex dset", "col"]]
)
def test_retrieve_additional_data_prompts_user_correctly(
    mocker, inputs, reg_mocked_with_params
):
    # Arrange
    m = MagicMock(side_effect=inputs)
    mocker.patch("builtins.input", m)
    reg = Registration(*reg_mocked_with_params)

    # Act
    reg.retrieve_additional_data()
    vals = [reg.name, reg.description, reg.location]

    # Assert
    assert vals == inputs


def test_request_approval_skips_if_approved(mocker, reg_mocked_with_params):
    # Arrange
    spy = mocker.patch(PATCH_REGISTRATION.format("approval_prompt"), return_value=True)
    reg = Registration(*reg_mocked_with_params)

    # Act
    reg.status = "APPROVED"

    # Assert
    spy.assert_not_called()


@pytest.mark.parametrize("approval", [True, False])
def test_request_approval_returns_users_input(mocker, approval, reg_mocked_with_params):
    # Arrange
    mocker.patch(PATCH_REGISTRATION.format("approval_prompt"), return_value=approval)
    mocker.patch(PATCH_REGISTRATION.format("dict_pretty_print"))
    mocker.patch("typer.echo")
    reg = Registration(*reg_mocked_with_params)

    # Act
    approved = reg.request_approval()

    # Assert
    assert approved == approval


@pytest.mark.parametrize("OUT_PATH", ["./test", "~/.medperf", "./workspace"])
@pytest.mark.parametrize("uid", [0, 12, 432])
def test_to_permanent_path_returns_expected_path(
    mocker, OUT_PATH, uid, reg_mocked_with_params
):
    # Arrange
    mocker.patch("os.rename")
    expected_path = os.path.join(str(Path(OUT_PATH).parent), str(uid))
    reg = Registration(*reg_mocked_with_params)

    # Act
    new_path = reg.to_permanent_path(OUT_PATH, uid)

    # Assert
    assert new_path == expected_path


@pytest.mark.parametrize(
    "OUT_PATH", ["test", "out", "out_path", "~/.medperf/data/tmp_0"]
)
@pytest.mark.parametrize("new_path", ["test", "new", "new_path", "~/.medperf/data/34"])
def test_to_permanent_path_renames_folder_correctly(
    mocker, OUT_PATH, new_path, reg_mocked_with_params
):
    # Arrange
    spy = mocker.patch("os.rename")
    mocker.patch("os.path.join", return_value=new_path)
    reg = Registration(*reg_mocked_with_params)

    # Act
    reg.to_permanent_path(OUT_PATH, 0)

    # Assert
    spy.assert_called_once_with(OUT_PATH, new_path)


@pytest.mark.parametrize("filepath", ["filepath"])
def test_write_writes_to_desired_file(mocker, filepath, reg_mocked_with_params):
    # Arrange
    spy = mocker.patch("os.path.join", return_value=filepath)
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.dump", MagicMock())
    reg = Registration(*reg_mocked_with_params)

    # Act
    path = reg.write("")

    # Assert
    assert path == filepath


@pytest.mark.parametrize("server_uid", [1, 4, 834, 12])
def test_upload_returns_uid_from_server(mocker, server_uid, reg_mocked_with_params):
    # Arrange
    server = Server("")
    mocker.patch(
        PATCH_REGISTRATION.format("Server.upload_dataset"), return_value=server_uid
    )
    reg = Registration(*reg_mocked_with_params)

    # Act
    uid = reg.upload(server)

    # Assert
    assert uid == server_uid


def test_is_registered_fails_when_uid_not_generated(mocker, reg_mocked_with_params):
    # Arrange
    reg = Registration(*reg_mocked_with_params)

    # Act & Assert
    with pytest.raises(KeyError):
        reg.is_registered()


def test_is_registered_retrieves_local_datasets(mocker, reg_mocked_with_params):
    # Arrange
    spy = mocker.patch(PATCH_REGISTRATION.format("Dataset.all"), return_values=[])
    reg = Registration(*reg_mocked_with_params)
    reg.uid = 1

    # Act
    reg.is_registered()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("dset_uids", [[1, 2, 3], [], [23, 5, 12]])
@pytest.mark.parametrize("uid", [1, 2, 3, 4, 5, 6])
def test_is_registered_finds_uid_in_dsets(
    mocker, dset_uids, uid, reg_mocked_with_params
):
    # Arrange
    dsets = [MockedDataset(dset_uid) for dset_uid in dset_uids]
    mocker.patch(PATCH_REGISTRATION.format("Dataset.all"), return_value=dsets)
    reg = Registration(*reg_mocked_with_params)
    reg.uid = uid

    # Act
    registered = reg.is_registered()

    # Assert
    assert registered == (uid in dset_uids)
