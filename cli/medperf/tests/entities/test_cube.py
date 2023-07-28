import os
import yaml
import pytest

import medperf
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.utils import storage_path
from medperf.tests.entities.utils import (
    setup_cube_fs,
    setup_cube_comms,
    setup_cube_comms_downloads,
)
from medperf.tests.mocks.pexpect import MockPexpect
from medperf.exceptions import ExecutionError

PATCH_CUBE = "medperf.entities.cube.{}"
DEFAULT_CUBE = {"id": 37}
NO_IMG_CUBE = {"id": 345, "image_tarball_url": None, "image_tarball_hash": None}


@pytest.fixture(params={"local": [1, 2, 3], "remote": [4, 5, 6], "user": [4]})
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

    # Mock additional third party elements
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("combine_proc_sp_text"), return_value="")

    return request.param


class TestGetFiles:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.id = setup["remote"][0]["id"]

        # Specify expected path for all downloaded files
        self.cube_path = os.path.join(storage_path(config.cubes_storage), str(self.id))
        self.manifest_path = os.path.join(self.cube_path, config.cube_filename)
        self.params_path = os.path.join(
            self.cube_path, config.workspace_path, config.params_filename
        )
        self.add_path = os.path.join(
            self.cube_path, config.additional_path, config.tarball_filename
        )
        self.img_path = os.path.join(self.cube_path, config.image_path, "img.tar.gz")
        self.file_paths = [
            self.manifest_path,
            self.params_path,
            self.add_path,
            self.img_path,
        ]

    @pytest.mark.parametrize("setup", [{"remote": [DEFAULT_CUBE]}], indirect=True)
    def test_get_cube_retrieves_files(self, setup):
        # Act
        Cube.get(self.id)

        # Assert
        for file in self.file_paths:
            assert os.path.exists(file) and os.path.isfile(file)

    @pytest.mark.parametrize("setup", [{"remote": [NO_IMG_CUBE]}], indirect=True)
    def test_get_cube_without_image_configures_mlcube(self, mocker, setup):
        # Arrange
        spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
        expected_cmd = f"mlcube configure --mlcube={self.manifest_path}"

        # Act
        Cube.get(self.id)

        # Assert
        spy.assert_called_once_with(expected_cmd)

    @pytest.mark.parametrize("setup", [{"remote": [DEFAULT_CUBE]}], indirect=True)
    def test_get_cube_with_image_isnt_configured(self, mocker, setup):
        # Arrange
        spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")

        # Act
        Cube.get(self.id)

        # Assert
        spy.assert_not_called()


@pytest.mark.parametrize("setup", [{"remote": [DEFAULT_CUBE]}], indirect=True)
@pytest.mark.parametrize("task", ["infer"])
class TestRun:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, setup):
        self.id = setup["remote"][0]["id"]
        self.platform = config.platform
        self.gpus = config.gpus

        # Specify expected path for the manifest files
        self.cube_path = os.path.join(storage_path(config.cubes_storage), str(self.id))
        self.manifest_path = os.path.join(self.cube_path, config.cube_filename)

    @pytest.mark.parametrize("timeout", [847, None])
    def test_cube_runs_command(self, mocker, timeout, setup, task):
        # Arrange
        mpexpect = MockPexpect(0)
        spy = mocker.patch(
            PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn
        )
        expected_cmd = (
            f"mlcube run --mlcube={self.manifest_path} --task={task}"
            + f"--platform={self.platform} --network=none"
        )

        # Act
        cube = Cube.get(self.id)
        cube.run(task, timeout=timeout)

        # Assert
        spy.assert_any_call(expected_cmd, timeout=timeout)

    def test_cube_runs_command_with_extra_args(self, mocker, setup, task):
        # Arrange
        mpexpect = MockPexpect(0)
        spy = mocker.patch("pexpect.spawn", side_effect=mpexpect.spawn)
        expected_cmd = (
            f"mlcube run --mlcube={self.manifest_path} --task={task} "
            + f'--platform={self.platform} test="test"'
        )

        # Act
        cube = Cube.get(self.id)
        cube.run(task, test="test")

        # Assert
        spy.assert_any_call(expected_cmd, timeout=None)

    def test_run_stops_execution_if_child_fails(self, mocker, setup, task):
        # Arrange
        mpexpect = MockPexpect(1)
        mocker.patch("pexpect.spawn", side_effect=mpexpect.spawn)

        # Act & Assert
        cube = Cube.get(self.id)
        with pytest.raises(ExecutionError):
            cube.run(task)


@pytest.mark.parametrize("setup", [{"local": [DEFAULT_CUBE]}], indirect=True)
@pytest.mark.parametrize("task", ["task"])
@pytest.mark.parametrize(
    "out_key,out_value",
    [["predictions_path", "preds"], ["path", {"default": "results"}]],
)
class TestDefaultOutput:
    @pytest.fixture(autouse=True)
    def set_common_attributes(self, fs, setup, task, out_key, out_value):
        self.id = setup["local"][0]["id"]

        # Create a manifest file with minimum required contents
        self.cube_contents = {
            "tasks": {task: {"parameters": {"outputs": {out_key: out_value}}}}
        }
        self.cube_path = os.path.join(storage_path(config.cubes_storage), str(self.id))
        self.manifest_path = os.path.join(self.cube_path, config.cube_filename)
        fs.create_file(self.manifest_path, contents=yaml.dump(self.cube_contents))

        # Construct the expected output path
        out_val_path = out_value
        if type(out_value) == dict:
            out_val_path = out_value["default"]
        self.output = os.path.join(self.cube_path, config.workspace_path, out_val_path)

    def test_default_output_returns_expected_path(self, task, out_key):
        # Arrange
        cube = Cube.get(self.id)

        # Act
        default_output = cube.get_default_output(task, out_key)

        # Assert
        assert default_output == self.output

    @pytest.mark.parametrize("param_key,param_val", [["key", "val"]])
    def test_default_output_returns_path_with_params(
        self, fs, task, out_key, param_key, param_val
    ):
        # Arrange
        # Create a params file with minimal content
        params_contents = {param_key: param_val}
        params_path = os.path.join(
            self.cube_path, config.workspace_path, config.params_filename
        )
        fs.create_file(params_path, contents=yaml.dump(params_contents))

        # Construct the expected path
        exp_path = os.path.join(self.output, param_val)

        # Act
        cube = Cube.get(self.id)
        out_path = cube.get_default_output(task, out_key, param_key)

        # Assert
        assert out_path == exp_path
