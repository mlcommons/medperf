from medperf.exceptions import InvalidArgumentError
from medperf.tests.mocks.cube import TestCube
import pytest
import medperf.commands.compatibility_test.utils as utils
import os
import medperf.config as config

PATCH_UTILS = "medperf.commands.compatibility_test.utils.{}"


class TestPrepareLocalCube:
    @pytest.fixture(autouse=True)
    def setup(self, mocker, fs):
        cube_path = "/path/to/cube"
        cube_path_config = os.path.join(cube_path, config.cube_filename)
        params_path = "/path/to/params.yaml"
        additional_path = "/path/to/additional"

        fs.create_file(
            cube_path_config,
            contents="tasks:\n  task1:\n    parameters:\n      key: value",
        )
        fs.create_file(params_path, contents="param1: value1\nparam2: value2")
        fs.create_dir(additional_path)

        mocker.patch(
            PATCH_UTILS.format("generate_tmp_path"), return_value="/tmp/params"
        )

        self.cube_path = cube_path
        self.cube_path_config = cube_path_config
        self.params_path = params_path
        self.additional_path = additional_path

    def test_prepare_local_cube_creates_cube_object(self):
        # Act
        cube = utils.prepare_local_cube(self.cube_path_config)

        # Assert
        assert isinstance(cube, utils.Cube)
        assert cube.for_test is True
        assert cube.name.startswith("local_")

    def test_prepare_local_cube_loads_container_config(self):
        # Act
        cube = utils.prepare_local_cube(self.cube_path_config)

        # Assert
        assert cube.container_config is not None
        assert "tasks" in cube.container_config

    def test_prepare_local_cube_loads_parameters_config(self):
        # Act
        cube = utils.prepare_local_cube(
            self.cube_path_config, parameters=self.params_path
        )

        # Assert
        assert cube.parameters_config is not None
        assert cube.parameters_config["param1"] == "value1"

    def test_prepare_local_cube_handles_no_parameters(self):
        # Act
        cube = utils.prepare_local_cube(self.cube_path_config)

        # Assert
        assert cube.parameters_config is None

    def test_prepare_local_cube_sets_params_path(self, mocker):
        # Arrange
        expected_path = "/tmp/test_params"
        mocker.patch(
            PATCH_UTILS.format("generate_tmp_path"), return_value=expected_path
        )

        # Act
        cube = utils.prepare_local_cube(self.cube_path_config)

        # Assert
        assert cube.params_path == expected_path

    def test_prepare_local_cube_sets_additional_files_folder(self):
        # Act
        cube = utils.prepare_local_cube(
            self.cube_path_config, additional=self.additional_path
        )

        # Assert
        assert cube.additional_files_folder_path == self.additional_path


class TestPrepareCube:
    @pytest.fixture(autouse=True)
    def setup(self, mocker, fs):
        cube_path = "/path/to/cube"
        cube_path_config = os.path.join(cube_path, config.cube_filename)
        fs.create_file(
            cube_path_config,
            contents="tasks:\n  task1:\n    parameters:\n      key: value",
        )

        mocker.patch(
            PATCH_UTILS.format("generate_tmp_path"), return_value="/tmp/params"
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
        spy_setup.assert_called_once_with(mock_cube, False, None)

    def test_prepare_cube_passes_local_only_to_server_cube(self, mocker):
        # Arrange
        uid = 5
        mock_cube = TestCube(id=uid)
        spy_get = mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=mock_cube)
        mocker.patch(PATCH_UTILS.format("setup_cube"), return_value=mock_cube)

        # Act
        utils.prepare_cube(uid, local_only=True)

        # Assert
        spy_get.assert_called_once_with(uid, local_only=True)

    def test_exception_is_raised_for_nonexisting_path(self):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            utils.prepare_cube("path/that/doesn't/exist")


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
        utils.setup_cube(mock_cube, use_local_container_image=True)

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
            use_local_container_image=True,
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
        utils.setup_cube(mock_cube, use_local_container_image=True)

        # Assert
        spy_store.assert_not_called()

    def test_setup_cube_returns_cube(self, mocker):
        # Arrange
        mock_cube = TestCube(id=1)
        mocker.patch.object(TestCube, "download_run_files")

        # Act
        result = utils.setup_cube(mock_cube, use_local_container_image=True)

        # Assert
        assert result == mock_cube
