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
