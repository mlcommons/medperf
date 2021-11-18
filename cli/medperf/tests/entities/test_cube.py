from medperf.entities import Server, Cube
from medperf.tests.mocks.requests import cube_metadata_generator
from medperf.tests.mocks.pexpect import MockPexpect
import medperf
from yaspin import yaspin

import pytest
from unittest.mock import MagicMock

PATCH_SERVER = "medperf.entities.benchmark.Server.{}"
PATCH_CUBE = "medperf.entities.cube.{}"
CUBE_PATH = "cube_path"
PARAMS_PATH = "params_path"
TARBALL_PATH = "tarball_path"
TARBALL_HASH = "tarball_hash"

TASK = "task"
OUT_KEY = "out_key"
VALUE = "value"
PARAM_KEY = "param_key"
PARAM_VALUE = "param_value"


@pytest.fixture
def server(mocker):
    server = Server("mock.url")
    mocker.patch(PATCH_SERVER.format("get_cube"), return_value=CUBE_PATH)
    mocker.patch(PATCH_SERVER.format("get_cube_params"), return_value=PARAMS_PATH)
    mocker.patch(PATCH_SERVER.format("get_cube_additional"), return_value=TARBALL_PATH)
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value=TARBALL_HASH)
    mocker.patch(PATCH_CUBE.format("untar_additional"))

    return server


@pytest.fixture
def basic_body(mocker):
    body_gen = cube_metadata_generator()
    mocker.patch(PATCH_SERVER.format("get_cube_metadata"), side_effect=body_gen)
    return body_gen


@pytest.fixture
def params_body(mocker):
    body_gen = cube_metadata_generator(with_params=True)
    mocker.patch(PATCH_SERVER.format("get_cube_metadata"), side_effect=body_gen)
    return body_gen


@pytest.fixture
def tar_body(mocker):
    body_gen = cube_metadata_generator(with_tarball=True)
    mocker.patch(PATCH_SERVER.format("get_cube_metadata"), side_effect=body_gen)
    return body_gen


def test_get_basic_cube_retrieves_metadata_from_server(mocker, server, basic_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.Server, "get_cube_metadata")

    # Act
    uid = 1
    Cube.get(uid, server)

    # Assert
    spy.assert_called_once_with(uid)


def test_get_basic_cube_retrieves_cube_manifest(mocker, server, basic_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.Server, "get_cube")

    # Act
    uid = 1
    body = basic_body(uid)
    Cube.get(uid, server)

    # Assert
    spy.assert_called_once_with(body["git_mlcube_url"], uid)


def test_get_basic_cube_doesnt_retrieve_parameters(mocker, server, basic_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.Server, "get_cube_params")

    # Act
    uid = 1
    Cube.get(uid, server)

    # Assert
    spy.assert_not_called()


def test_get_basic_cube_doesnt_retrieve_tarball(mocker, server, basic_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.Server, "get_cube_additional")

    # Act
    uid = 1
    Cube.get(uid, server)

    # Assert
    spy.assert_not_called()


def test_get_cube_with_parameters_retrieves_parameters(mocker, server, params_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.Server, "get_cube_params")

    # Act
    uid = 1
    body = params_body(uid)
    Cube.get(uid, server)

    # Assert
    spy.assert_called_once_with(body["git_parameters_url"], uid)


def test_get_cube_with_tarball_retrieves_tarball(mocker, server, tar_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.Server, "get_cube_additional")

    # Act
    uid = 1
    body = tar_body(uid)
    Cube.get(uid, server)

    # Assert
    spy.assert_called_once_with(body["tarball_url"], uid)


def test_get_cube_with_tarball_generates_TARBALL_HASH(mocker, server, tar_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "get_file_sha1")

    # Act
    uid = 1
    Cube.get(uid, server)

    # Assert
    spy.assert_called_once_with(TARBALL_PATH)


def test_get_cube_with_tarball_untars_files(mocker, server, tar_body):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "untar_additional")

    # Act
    uid = 1
    Cube.get(uid, server)

    # Assert
    spy.assert_called_once_with(TARBALL_PATH)


def test_cube_is_valid_if_no_tarball(mocker, server, basic_body):
    # Act
    uid = 1
    cube = Cube.get(uid, server)

    # Assert
    assert cube.is_valid()


def test_cube_is_valid_with_correct_hash(mocker, server, tar_body):
    # Act
    uid = 1
    cube = Cube.get(uid, server)

    # Assert
    assert cube.is_valid()


def test_cube_is_invalid_with_incorrect_hash(mocker, server, tar_body):
    # Arrange
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value="incorrect_hash")

    # Act
    uid = 1
    cube = Cube.get(uid, server)

    # Assert
    assert not cube.is_valid()


def test_cube_runs_command_with_pexpect(mocker, server, basic_body):
    # Arrange
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=MockPexpect.spawn)
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
    sp = yaspin()
    TASK = "TASK"
    expected_cmd = f"mlcube run --mlcube={CUBE_PATH} --task={TASK}"

    # Act
    uid = 1
    cube = Cube.get(uid, server)
    cube.run(sp, "TASK")

    # Assert
    spy.assert_called_once_with(expected_cmd)


def test_cube_runs_command_with_extra_args(mocker, server, basic_body):
    # Arrange
    spy = mocker.patch(
        PATCH_CUBE.format("pexpect.spawn"), side_effect=MockPexpect.spawn
    )
    sp = yaspin()
    TASK = "TASK"
    expected_cmd = f"mlcube run --mlcube={CUBE_PATH} --task={TASK} test=test"

    # Act
    uid = 1
    cube = Cube.get(uid, server)
    cube.run(sp, "TASK", test="test")

    # Assert
    spy.assert_called_once_with(expected_cmd)


def test_default_output_reads_cube_manifest(mocker, server, basic_body):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    spy = mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.full_load"), m)

    # Act
    uid = 1
    cube = Cube.get(uid, server)
    cube.get_default_output(TASK, OUT_KEY)

    # Assert
    spy.assert_called_once_with(CUBE_PATH, "r")


def test_default_output_returns_specified_path(mocker, server, basic_body):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.full_load"), m)

    exp_path = f"./workspace/{VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid, server)
    out_path = cube.get_default_output(TASK, OUT_KEY)

    # Assert
    assert out_path == exp_path


def test_default_output_returns_specified_dict_path(mocker, server, basic_body):
    # Arrange
    cube_contents = {
        "tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: {"default": VALUE}}}}}
    }
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.full_load"), m)

    exp_path = f"./workspace/{VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid, server)
    out_path = cube.get_default_output(TASK, OUT_KEY)

    # Assert
    assert out_path == exp_path


def test_default_output_returns_path_with_params(mocker, server, params_body):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    params_contents = {PARAM_KEY: PARAM_VALUE}
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents, params_contents])
    mocker.patch(PATCH_CUBE.format("yaml.full_load"), m)

    exp_path = f"./workspace/{VALUE}/{PARAM_VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid, server)
    out_path = cube.get_default_output(TASK, OUT_KEY, PARAM_KEY)

    # Assert
    assert out_path == exp_path
