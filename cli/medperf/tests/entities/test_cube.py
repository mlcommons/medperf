import os
import pytest

import medperf.config as config
from medperf.entities.cube import Cube
from medperf.containers.runners.runner import Runner
from medperf.tests.entities.utils import (
    setup_cube_fs,
    setup_cube_comms,
    setup_cube_comms_downloads,
)
from medperf.exceptions import InvalidEntityError
from medperf.entities.encrypted_container_key import EncryptedKey
from medperf.tests.mocks.cube import TestCube

PATCH_CUBE = "medperf.entities.cube.{}"
PATCH_CUBE_UTILS = "medperf.entities.cube_utils.{}"
DEFAULT_CUBE = {"id": 37}
NO_IMG_CUBE = {
    "id": 345,
    "image_tarball_url": None,
    "image_tarball_hash": None,
    "image_hash": "hash",
}


@pytest.fixture
def runner(mocker):
    runner_ = mocker.create_autospec(spec=Runner)
    return runner_


@pytest.fixture(
    params={
        "unregistered": ["c1", "c2"],
        "local": ["c1", "c2", 1, 2, 3],
        "remote": [1, 2, 3, 4, 5, 6],
        "user": [4],
    }
)
def setup(request, mocker, comms, fs):
    local_ents = request.param.get("local", [])
    remote_ents = request.param.get("remote", [])
    user_ents = request.param.get("user", [])
    # Have a list that will contain all uploaded entities of the given type
    uploaded = []

    setup_cube_fs(local_ents, fs)
    setup_cube_comms(mocker, comms, remote_ents, user_ents, uploaded)
    setup_cube_comms_downloads(mocker, fs)
    request.param["uploaded"] = uploaded

    return request.param


class TestGetFiles:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.id = setup["remote"][0]["id"]

        # Specify expected path for all downloaded files
        self.cube_path = os.path.join(config.cubes_folder, str(self.id))
        self.manifest_path = os.path.join(self.cube_path, config.cube_filename)
        self.params_path = os.path.join(
            self.cube_path, config.workspace_path, config.params_filename
        )
        self.add_path = os.path.join(
            self.cube_path, config.additional_path, config.tarball_filename
        )
        self.config_files_paths = [self.manifest_path, self.params_path]
        self.run_files_paths = [self.add_path]

    @pytest.mark.parametrize("setup", [{"remote": [DEFAULT_CUBE]}], indirect=True)
    def test_get_cube_retrieves_files(self, setup):
        # Act
        Cube.get(self.id)

        # Assert
        for file in self.config_files_paths:
            assert os.path.exists(file) and os.path.isfile(file)
        for file in self.run_files_paths:
            assert not os.path.exists(file)

    @pytest.mark.parametrize("setup", [{"remote": [DEFAULT_CUBE]}], indirect=True)
    def test_download_run_files_retrieves_files(self, mocker, setup, runner):
        # Act
        cube = Cube.get(self.id)
        cube._runner = runner
        spy = mocker.patch.object(cube.runner, "download")
        cube.download_run_files()

        # Assert
        for file in self.config_files_paths + self.run_files_paths:
            assert os.path.exists(file)
        assert spy.called_once()


@pytest.mark.parametrize("destroy_key", [True, False])
def test_run_key_destruction_encrypted(mocker, fs, destroy_key):
    # Arrange
    cube = TestCube()

    # encrypted case
    mocker.patch.object(cube, "is_encrypted", return_value=True)

    # mock runner
    mocker.patch.object(cube, "_runner", mocker.Mock())

    # spy on remove_path
    remove_path_spy = mocker.patch(PATCH_CUBE.format("remove_path"))

    # mock __get_decryption_key
    get_key_spy = mocker.patch.object(cube, "_Cube__get_decryption_key")
    fake_key = "tmp/keyfile"
    get_key_spy.return_value = (fake_key, destroy_key)

    # Act
    cube.run(task="infer")

    # Assert
    get_key_spy.assert_called_once()

    if destroy_key:
        remove_path_spy.assert_called_once_with(fake_key, sensitive=True)
    else:
        remove_path_spy.assert_not_called()


def test_run_unencrypted_skips_decryption_key(mocker):
    # Arrange
    cube = TestCube()

    # unencrypted
    mocker.patch.object(cube, "is_encrypted", return_value=False)

    # mock runner
    mocker.patch.object(cube, "_runner", mocker.Mock())

    # spy on key retrieval + removal
    get_key_spy = mocker.patch.object(cube, "_Cube__get_decryption_key")
    remove_path_spy = mocker.patch(PATCH_CUBE.format("remove_path"))

    # Act
    cube.run(task="infer")

    # Assert
    get_key_spy.assert_not_called()
    remove_path_spy.assert_not_called()


# -------------------------------------------------------------------
# __get_decryption_key
# -------------------------------------------------------------------
def test_get_key_not_logged_in_returns_local_and_no_destroy(mocker, fs):
    # Arrange
    cube = Cube(id=1, name="c", owner=10, git_mlcube_url="x")

    mocker.patch(PATCH_CUBE.format("is_user_logged_in"), return_value=False)
    key_path = "/keylocal"
    fs.create_file(key_path, contents="k")
    mocker.patch(
        PATCH_CUBE.format("Cube._Cube__get_decryption_key_from_filesystem"),
        return_value=key_path,
    )

    # Act
    key, destroy = cube._Cube__get_decryption_key()

    # Assert
    assert key == key_path
    assert destroy is False


def test_get_key_logged_in_as_owner_returns_local(mocker, fs):
    cube = Cube(id=1, name="c", owner=99, git_mlcube_url="x")

    mocker.patch(PATCH_CUBE.format("is_user_logged_in"), return_value=True)
    mocker.patch(PATCH_CUBE.format("get_medperf_user_data"), return_value={"id": 99})

    key_path = "/localkey"
    fs.create_file(key_path, contents="x")
    mocker.patch(
        PATCH_CUBE.format("Cube._Cube__get_decryption_key_from_filesystem"),
        return_value=key_path,
    )

    # Act
    key, destroy = cube._Cube__get_decryption_key()

    # Assert
    assert key == key_path
    assert destroy is False


def test_get_key_logged_in_not_owner_returns_server_key(mocker):
    cube = Cube(id=1, name="c", owner=123, git_mlcube_url="x")

    mocker.patch(PATCH_CUBE.format("is_user_logged_in"), return_value=True)
    mocker.patch(PATCH_CUBE.format("get_medperf_user_data"), return_value={"id": 999})

    mock_server_key = "/serverkey"
    mocker.patch(
        PATCH_CUBE.format("Cube._Cube__get_decryption_key_from_server"),
        return_value=mock_server_key,
    )

    # Act
    key, destroy = cube._Cube__get_decryption_key()

    # Assert
    assert key == mock_server_key
    assert destroy is True


# -------------------------------------------------------------------
# __get_decryption_key_from_filesystem
# -------------------------------------------------------------------
def test_get_fs_key_exists(mocker, fs):
    cube = Cube(id=1, name="c", git_mlcube_url="x", owner=5)

    key_path = "/keys/1.key"
    fs.create_file(key_path, contents="q")

    mocker.patch(PATCH_CUBE.format("get_decryption_key_path"), return_value=key_path)

    # Act
    result = cube._Cube__get_decryption_key_from_filesystem()

    # Assert
    assert result == key_path


def test_get_fs_key_missing_raises(mocker):
    cube = Cube(id=1, name="c", git_mlcube_url="x", owner=5)

    mocker.patch(PATCH_CUBE.format("get_decryption_key_path"), return_value="/missing")

    # Act + Assert
    with pytest.raises(InvalidEntityError):
        cube._Cube__get_decryption_key_from_filesystem()


# -------------------------------------------------------------------
# __get_decryption_key_from_server
# -------------------------------------------------------------------
def test_get_key_from_server_calls_encryptedkey(mocker):
    cube = Cube(id=1, name="c", git_mlcube_url="x", owner=5)

    mock_key = mocker.Mock()
    mock_key.decrypt.return_value = "/tmp/dec"
    mocker.patch.object(EncryptedKey, "get_user_container_key", return_value=mock_key)

    # Act
    result = cube._Cube__get_decryption_key_from_server()

    # Assert
    assert result == "/tmp/dec"
    mock_key.decrypt.assert_called_once()
