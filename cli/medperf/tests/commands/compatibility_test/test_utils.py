from medperf.exceptions import InvalidArgumentError
import pytest

import medperf.commands.compatibility_test.utils as utils
import os
from medperf import settings


PATCH_UTILS = "medperf.commands.compatibility_test.utils.{}"


class TestPrepareCube:
    @pytest.fixture(autouse=True)
    def setup(self, fs):
        cube_path = "/path/to/cube"
        cube_path_config = os.path.join(cube_path, settings.cube_filename)
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
        cube_path = os.path.join(settings.cubes_folder, new_uid)
        assert os.path.islink(cube_path)
        assert os.path.realpath(cube_path) == os.path.realpath(self.cube_path)

    def test_local_cube_metadata_is_created(self):
        # Act
        new_uid = utils.prepare_cube(self.cube_path)

        # Assert
        metadata_file = os.path.join(
            settings.cubes_folder,
            new_uid,
            settings.cube_metadata_filename,
        )

        assert os.path.exists(metadata_file)

    def test_local_cube_metadata_is_not_created_if_found(self, fs):
        # Arrange
        metadata_file = os.path.join(self.cube_path, settings.cube_metadata_filename)

        metadata_contents = "meta contents before execution"

        fs.create_file(metadata_file, contents=metadata_contents)

        # Act
        new_uid = utils.prepare_cube(self.cube_path)

        # Assert
        metadata_file = os.path.join(
            settings.cubes_folder,
            new_uid,
            settings.cube_metadata_filename,
        )
        assert open(metadata_file).read() == metadata_contents

    def test_exception_is_raised_for_nonexisting_path(self):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            utils.prepare_cube("path/that/doesn't/exist")

    def test_cleanup_is_set_up_correctly(self):
        # Act
        uid = utils.prepare_cube(self.cube_path)
        symlinked_path = os.path.join(settings.cubes_folder, uid)
        metadata_file = os.path.join(
            self.cube_path,
            settings.cube_metadata_filename,
        )
        # Assert
        assert set([symlinked_path, metadata_file]).issubset(settings.tmp_paths)
