from medperf.exceptions import InvalidArgumentError
from medperf.tests.mocks.cube import TestCube
import pytest

import medperf.commands.compatibility_test.utils as utils
import os
import medperf.config as config
from pytest_mock import MockerFixture
from medperf.tests.mocks.cube import TestCube

PATCH_UTILS = "medperf.commands.compatibility_test.utils.{}"


class TestPrepareCube:
    @pytest.fixture(autouse=True)
    def setup(self, mocker: MockerFixture, fs):
        cube_path = "/path/to/cube"
        cube_path_config = os.path.join(cube_path, config.cube_filename)
        fs.create_file(cube_path_config, contents="cube mlcube.yaml contents")
        mocker.patch(PATCH_UTILS.format('load_yaml_content'), return_value=TestCube().todict())
        self.cube_path = cube_path
        self.cube_path_config = cube_path_config

    @pytest.mark.parametrize("uid", [1, "4"])
    def test_server_cube_uid_is_returned_if_passed(self, uid):
        # Act
        returned_uid = utils.prepare_cube(uid)

        # Assert
        assert returned_uid == uid

    def test_local_cube_symlink_is_created_properly(self):
        # Act
        new_uid = utils.prepare_cube(self.cube_path_config)

        # Assert
        cube_path = os.path.join(config.cubes_folder, new_uid)
        assert os.path.islink(cube_path)
        assert os.path.realpath(cube_path) == os.path.realpath(self.cube_path)

    def test_local_cube_metadata_is_created(self):
        # Act
        new_uid = utils.prepare_cube(self.cube_path_config)

        # Assert
        metadata_file = os.path.join(
            config.cubes_folder,
            new_uid,
            config.cube_metadata_filename,
        )

        assert os.path.exists(metadata_file)

    def test_local_cube_metadata_is_not_created_if_found(self, fs):
        # Arrange
        metadata_file = os.path.join(self.cube_path, config.cube_metadata_filename)

        metadata_contents = "meta contents before execution"

        fs.create_file(metadata_file, contents=metadata_contents)

        # Act
        new_uid = utils.prepare_cube(self.cube_path_config)

        # Assert
        metadata_file = os.path.join(
            config.cubes_folder,
            new_uid,
            config.cube_metadata_filename,
        )
        assert open(metadata_file).read() == metadata_contents

    def test_exception_is_raised_for_nonexisting_path(self):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            utils.prepare_cube("path/that/doesn't/exist")

    def test_cleanup_is_set_up_correctly(self):
        # Act
        uid = utils.prepare_cube(self.cube_path_config)
        symlinked_path = os.path.join(config.cubes_folder, uid)
        metadata_file = os.path.join(
            self.cube_path,
            config.cube_metadata_filename,
        )
        # Assert
        assert set([symlinked_path, metadata_file]).issubset(config.tmp_paths)


def test_get_cube_downloads_files(mocker):
    mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=TestCube(id=1))
    spy_download = mocker.patch.object(TestCube, "download_run_files")

    uid = 1
    name = "test-cube"

    utils.get_cube(uid, name)

    spy_download.assert_called_once()


def test_get_cube_uses_local_model_image(mocker):
    mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=TestCube(id=1))
    spy_download = mocker.patch.object(TestCube, "download_run_files")

    utils.get_cube(1, "test-cube", use_local_model_image=True)

    spy_download.assert_not_called()


def test_get_cube_stores_decryption_key(mocker):
    mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=TestCube(id=5))
    spy_store = mocker.patch(
        PATCH_UTILS.format("store_decryption_key"), return_value="/tmp/dummy_key_path"
    )

    dummy_path = "/tmp/somekey.key"

    utils.get_cube(
        5,
        "secure-cube",
        decryption_key_file_path=dummy_path,
        use_local_model_image=True,
    )

    spy_store.assert_called_once_with(5, dummy_path)
    assert "/tmp/dummy_key_path" in config.sensitive_tmp_paths
