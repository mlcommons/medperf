from medperf.exceptions import InvalidArgumentError
from medperf.tests.mocks.cube import TestCube
import pytest
import medperf.commands.compatibility_test.utils as utils
import os
import medperf.config as config

PATCH_UTILS = "medperf.commands.compatibility_test.utils.{}"


class TestPrepareCube:
    @pytest.fixture(autouse=True)
    def setup(self, mocker, fs):
        cube_path = "/path/to/cube"
        cube_path_config = os.path.join(cube_path, config.cube_filename)
        fs.create_file(
            cube_path_config,
            contents="tasks:\n  task1:\n    parameters:\n      key: value",
        )

        self.cube_path = cube_path
        self.cube_path_config = cube_path_config

    @pytest.mark.parametrize("uid", [1, "4"])
    def test_server_cube_is_retrieved_if_uid_passed(self, mocker, uid):
        # Arrange
        mock_cube = TestCube(id=uid)
        mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=mock_cube)
        spy_setup = mocker.patch(
            PATCH_UTILS.format("setup_cube"), return_value=mock_cube
        )

        # Act
        returned_cube = utils.prepare_cube(uid)

        # Assert
        assert returned_cube == mock_cube
        spy_setup.assert_called_once_with(mock_cube, None)


class TestSetupCube:
    def test_setup_cube_downloads_files_by_default(self, mocker):
        # Arrange
        mock_cube = TestCube(id=1)
        spy_download = mocker.patch.object(TestCube, "download_run_files")

        # Act
        utils.setup_cube(mock_cube)

        # Assert
        spy_download.assert_called_once()

    def test_setup_cube_skips_download_with_local_image(self, mocker):
        # Arrange
        mock_cube = TestCube(id=1)
        spy_download = mocker.patch.object(TestCube, "download_run_files")

        # Act
        utils.setup_cube(mock_cube, download=False)

        # Assert
        spy_download.assert_not_called()

    def test_setup_cube_stores_decryption_key(self, mocker):
        # Arrange
        mock_cube = TestCube(id=5)
        mock_cube.identifier = 5
        dummy_key_path = "/tmp/somekey.key"
        stored_key_path = "/tmp/stored_key_path"

        spy_store = mocker.patch(
            PATCH_UTILS.format("store_decryption_key"), return_value=stored_key_path
        )
        mocker.patch.object(TestCube, "download_run_files")

        # Act
        utils.setup_cube(
            mock_cube,
            decryption_key_file_path=dummy_key_path,
        )

        # Assert
        spy_store.assert_called_once_with(5, dummy_key_path)
        assert stored_key_path in config.sensitive_tmp_paths

    def test_setup_cube_handles_no_decryption_key(self, mocker):
        # Arrange
        mock_cube = TestCube(id=1)
        spy_store = mocker.patch(PATCH_UTILS.format("store_decryption_key"))
        mocker.patch.object(TestCube, "download_run_files")

        # Act
        utils.setup_cube(mock_cube)

        # Assert
        spy_store.assert_not_called()

    def test_setup_cube_returns_cube(self, mocker):
        # Arrange
        mock_cube = TestCube(id=1)
        mocker.patch.object(TestCube, "download_run_files")

        # Act
        result = utils.setup_cube(mock_cube)

        # Assert
        assert result == mock_cube
