import pytest
from unittest.mock import MagicMock

import medperf
from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Cube
from medperf.tests.mocks.pexpect import MockPexpect
from medperf.tests.mocks.requests import cube_metadata_generator

patch_cube = "medperf.entities.cube.{}"
cube_path = "cube_path"
params_path = "params_path"
tarball_path = "tarball_path"
tarball_hash = "tarball_hash"

task = "task"
out_key = "out_key"
value = "value"
param_key = "param_key"
param_value = "param_value"


@pytest.fixture
def ui(mocker):
    ui = mocker.create_autospec(spec=UI)
    return ui


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    mocker.patch.object(comms, "get_cube", return_value=cube_path)
    mocker.patch.object(comms, "get_cube_params", return_value=params_path)
    mocker.patch.object(comms, "get_cube_additional", return_value=tarball_path)
    mocker.patch(patch_cube.format("get_file_sha1"), return_value=tarball_hash)
    mocker.patch(patch_cube.format("untar_additional"))

    return comms


@pytest.fixture
def basic_body(mocker, comms):
    body_gen = cube_metadata_generator()
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    return body_gen


@pytest.fixture
def params_body(mocker, comms):
    body_gen = cube_metadata_generator(with_params=True)
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    return body_gen


@pytest.fixture
def tar_body(mocker, comms):
    body_gen = cube_metadata_generator(with_tarball=True)
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    return body_gen


def test_get_basic_cube_retrieves_metadata_from_comms(mocker, comms, basic_body):
    # Arrange
    spy = mocker.spy(comms, "get_cube_metadata")

    # Act
    uid = 1
    Cube.get(uid, comms)

    # Assert
    spy.assert_called_once_with(uid)


def test_get_basic_cube_retrieves_cube_manifest(mocker, comms, basic_body):
    # Arrange
    spy = mocker.spy(comms, "get_cube")

    # Act
    uid = 1
    body = basic_body(uid)
    Cube.get(uid, comms)

    # Assert
    spy.assert_called_once_with(body["git_mlcube_url"], uid)


def test_get_basic_cube_doesnt_retrieve_parameters(mocker, comms, basic_body):
    # Arrange
    spy = mocker.spy(comms, "get_cube_params")

    # Act
    uid = 1
    Cube.get(uid, comms)

    # Assert
    spy.assert_not_called()


def test_get_basic_cube_doesnt_retrieve_tarball(mocker, comms, basic_body):
    # Arrange
    spy = mocker.spy(comms, "get_cube_additional")

    # Act
    uid = 1
    Cube.get(uid, comms)

    # Assert
    spy.assert_not_called()


def test_get_cube_with_parameters_retrieves_parameters(mocker, comms, params_body):
    # Arrange
    spy = mocker.spy(comms, "get_cube_params")

    # Act
    uid = 1
    body = params_body(uid)
    Cube.get(uid, comms)

    # Assert
    spy.assert_called_once_with(body["git_parameters_url"], uid)


def test_get_cube_with_tarball_retrieves_tarball(mocker, comms, tar_body):
    # Arrange
    spy = mocker.spy(comms, "get_cube_additional")

    # Act
    uid = 1
    body = tar_body(uid)
    Cube.get(uid, comms)

    # Assert
    spy.assert_called_once_with(body["tarball_url"], uid)


def test_get_cube_with_tarball_generates_tarball_hash(mocker, comms, tar_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "get_file_sha1")

    # Act
    uid = 1
    Cube.get(uid, comms)

    # Assert
    spy.assert_called_once_with(tarball_path)


def test_get_cube_with_tarball_untars_files(mocker, comms, tar_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "untar_additional")

    # Act
    uid = 1
    Cube.get(uid, comms)

    # Assert
    spy.assert_called_once_with(tarball_path)


def test_cube_is_valid_if_no_tarball(mocker, comms, basic_body):
    # Act
    uid = 1
    cube = Cube.get(uid, comms)

    # Assert
    assert cube.is_valid()


def test_cube_is_valid_with_correct_hash(mocker, comms, tar_body):
    # Act
    uid = 1
    cube = Cube.get(uid, comms)

    # Assert
    assert cube.is_valid()


def test_cube_is_invalid_with_incorrect_hash(mocker, comms, tar_body):
    # Arrange
    mocker.patch(patch_cube.format("get_file_sha1"), return_value="incorrect_hash")

    # Act
    uid = 1
    cube = Cube.get(uid, comms)

    # Assert
    assert not cube.is_valid()


def test_cube_runs_command_with_pexpect(mocker, ui, comms, basic_body):
    # Arrange
    mpexpect = MockPexpect(0)
    mocker.patch(patch_cube.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
    task = "task"
    expected_cmd = f"mlcube run --mlcube={cube_path} --task={task}"

    # Act
    uid = 1
    cube = Cube.get(uid, comms)
    cube.run(ui, "task")

    # Assert
    spy.assert_called_once_with(expected_cmd)


def test_cube_runs_command_with_extra_args(mocker, ui, comms, basic_body):
    # Arrange
    mpexpect = MockPexpect(0)
    spy = mocker.patch("pexpect.spawn", side_effect=mpexpect.spawn)
    task = "task"
    expected_cmd = f"mlcube run --mlcube={cube_path} --task={task} test=test"

    # Act
    uid = 1
    cube = Cube.get(uid, comms)
    cube.run(ui, task, test="test")

    # Assert
    spy.assert_called_once_with(expected_cmd)


def test_run_stops_execution_if_child_fails(mocker, ui, comms, basic_body):
    # Arrange
    mpexpect = MockPexpect(1)
    mocker.patch("pexpect.spawn", side_effect=mpexpect.spawn)
    spy = mocker.patch(
        patch_cube.format("pretty_error"), side_effect=lambda *args, **kwargs: exit()
    )
    task = "task"

    # Act
    uid = 1
    cube = Cube.get(uid, comms)
    with pytest.raises(SystemExit):
        cube.run(ui, task)

    # Assert
    spy.assert_called_once()


def test_default_output_reads_cube_manifest(mocker, comms, basic_body):
    # Arrange
    cube_contents = {"tasks": {task: {"parameters": {"outputs": {out_key: value}}}}}
    spy = mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(patch_cube.format("yaml.full_load"), m)

    # Act
    uid = 1
    cube = Cube.get(uid, comms)
    cube.get_default_output(task, out_key)

    # Assert
    spy.assert_called_once_with(cube_path, "r")


def test_default_output_returns_specified_path(mocker, comms, basic_body):
    # Arrange
    cube_contents = {"tasks": {task: {"parameters": {"outputs": {out_key: value}}}}}
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(patch_cube.format("yaml.full_load"), m)

    exp_path = f"./workspace/{value}"

    # Act
    uid = 1
    cube = Cube.get(uid, comms)
    out_path = cube.get_default_output(task, out_key)

    # Assert
    assert out_path == exp_path


def test_default_output_returns_specified_dict_path(mocker, comms, basic_body):
    # Arrange
    cube_contents = {
        "tasks": {task: {"parameters": {"outputs": {out_key: {"default": value}}}}}
    }
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(patch_cube.format("yaml.full_load"), m)

    exp_path = f"./workspace/{value}"

    # Act
    uid = 1
    cube = Cube.get(uid, comms)
    out_path = cube.get_default_output(task, out_key)

    # Assert
    assert out_path == exp_path


def test_default_output_returns_path_with_params(mocker, comms, params_body):
    # Arrange
    cube_contents = {"tasks": {task: {"parameters": {"outputs": {out_key: value}}}}}
    params_contents = {param_key: param_value}
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents, params_contents])
    mocker.patch(patch_cube.format("yaml.full_load"), m)

    exp_path = f"./workspace/{value}/{param_value}"

    # Act
    uid = 1
    cube = Cube.get(uid, comms)
    out_path = cube.get_default_output(task, out_key, param_key)

    # Assert
    assert out_path == exp_path
