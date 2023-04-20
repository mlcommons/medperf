from medperf.exceptions import InvalidArgumentError, InvalidEntityError
from medperf.tests.mocks.cube import TestCube
import pytest

import medperf.commands.compatibility_test.utils as utils
from medperf.utils import init_storage, storage_path
import os
import medperf.config as config


PATCH_UTILS = "medperf.commands.compatibility_test.utils.{}"


class TestPrepareCube:
    @pytest.fixture(autouse=True)
    def setup(self, fs):
        init_storage()
        cube_path = "path/to/cube"
        cube_path_config = os.path.join(cube_path, config.cube_filename)
        fs.create_file(cube_path_config, contents="cube mlcube.yaml contents")

        self.cube_path = cube_path
        self.cube_path_config = cube_path_config

    @pytest.mark.parametrize("uid", [1, "4"])
    def test_server_cube_uid_is_returned_if_passed(self, uid):
        # Act
        returned_uid = utils.prepare_cube(uid)

        # Assert
        assert returned_uid == uid

    @pytest.mark.parametrize("path_attr", ["cube_path", "cube_path_config"])
    def test_local_cube_symlink_is_created_properly(self, path_attr):
        # Act
        new_uid = utils.prepare_cube(getattr(self, path_attr))

        # Assert
        cube_storage_path = os.path.join(storage_path(config.cubes_storage), new_uid)
        assert os.path.islink(cube_storage_path)
        assert os.path.realpath(cube_storage_path) == os.path.realpath(self.cube_path)

    def test_local_cube_metadata_and_hashes_files_are_created(self):
        # Act
        new_uid = utils.prepare_cube(self.cube_path)

        # Assert
        metadata_file = os.path.join(
            storage_path(config.cubes_storage), new_uid, config.cube_metadata_filename,
        )
        hashes_file = os.path.join(
            storage_path(config.cubes_storage), new_uid, config.cube_hashes_filename,
        )

        assert os.path.exists(metadata_file)
        assert os.path.exists(hashes_file)

    def test_local_cube_metadata_and_hashes_files_are_not_created_if_found(self, fs):
        # Arrange
        metadata_file = os.path.join(self.cube_path, config.cube_metadata_filename)
        hashes_file = os.path.join(self.cube_path, config.cube_hashes_filename)

        metadata_contents = "meta contents before execution"
        hashes_contents = "hashes contents before execution"

        fs.create_file(metadata_file, contents=metadata_contents)
        fs.create_file(hashes_file, contents=hashes_contents)

        # Act
        new_uid = utils.prepare_cube(self.cube_path)

        # Assert
        metadata_file = os.path.join(
            storage_path(config.cubes_storage), new_uid, config.cube_metadata_filename,
        )
        hashes_file = os.path.join(
            storage_path(config.cubes_storage), new_uid, config.cube_hashes_filename,
        )
        assert open(metadata_file).read() == metadata_contents
        assert open(hashes_file).read() == hashes_contents

    def test_exception_is_raised_for_nonexisting_path(self):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            utils.prepare_cube("path/that/doesn't/exist")


def test_download_demo_dataset_fails_for_invalid_hash(mocker):
    # Arrange
    mocker.patch(PATCH_UTILS.format("resources.get_benchmark_demo_dataset"))
    mocker.patch(PATCH_UTILS.format("get_file_sha1"), return_value="incorrect hash")

    # Act & Assert
    with pytest.raises(InvalidEntityError):
        utils.download_demo_data("url", "correct hash")


def test_get_cube_fails_for_invalid_cube(mocker, ui):
    # Arrange
    invalid_cube = TestCube(is_valid=False)
    mocker.patch(PATCH_UTILS.format("Cube.get"), return_value=invalid_cube)

    # Act & Assert
    with pytest.raises(InvalidEntityError):
        utils.get_cube("id", "name")
