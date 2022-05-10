import os
import pytest
from unittest.mock import MagicMock, mock_open, ANY

import medperf
from medperf.ui.interface import UI
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.entities.cube import Cube
from medperf.utils import storage_path
from medperf.tests.utils import rand_l
from medperf.tests.mocks import Benchmark
from medperf.tests.mocks.pexpect import MockPexpect
from medperf.tests.mocks.requests import cube_metadata_generator

PATCH_SERVER = "medperf.entities.benchmark.Comms.{}"
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
def ui(mocker):
    ui = mocker.create_autospec(spec=UI)
    return ui


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    mocker.patch.object(comms, "get_cube", return_value=CUBE_PATH)
    mocker.patch.object(comms, "get_cube_params", return_value=PARAMS_PATH)
    mocker.patch.object(comms, "get_cube_additional", return_value=TARBALL_PATH)
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value=TARBALL_HASH)
    mocker.patch(PATCH_CUBE.format("untar"))

    return comms


@pytest.fixture
def no_local(mocker):
    mocker.patch(PATCH_CUBE.format("Cube.all"), return_value=[])


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


def test_all_looks_for_cubes_in_correct_path(mocker):
    # Arrange
    cubes_path = storage_path(config.cubes_storage)
    fs = iter([(".", (), ())])
    spy = mocker.patch("os.walk", return_value=fs)

    # Act
    Cube.all(ui)

    # Assert
    spy.assert_called_once_with(cubes_path)


@pytest.mark.parametrize("cube_uid", rand_l(1, 500, 3))
def test_all_reads_local_cube_metadata(mocker, cube_uid):
    # Arrange
    cube_uid = str(cube_uid)
    cubes_path = storage_path(config.cubes_storage)
    fs = iter([(".", (cube_uid,), ())])
    mocker.patch("os.walk", return_value=fs)
    spy = mocker.patch("builtins.open", mock_open())
    cube_meta = cube_metadata_generator()(cube_uid)
    mocker.patch("yaml.safe_load", return_value=cube_meta)

    exp_path = os.path.join(cubes_path, cube_uid, config.cube_filename)

    # Act
    Cube.all(ui)

    # Assert
    spy.assert_called_once_with(exp_path, "r")


@pytest.mark.parametrize("cube_uid", rand_l(1, 500, 3))
@pytest.mark.parametrize("with_params", [True, False])
def test_all_creates_cube_with_expected_content(mocker, cube_uid, with_params):
    # Arrange
    cube_uid = str(cube_uid)
    cubes_path = storage_path(config.cubes_storage)
    fs = iter([(".", (cube_uid,), ())])
    mocker.patch("os.walk", return_value=fs)
    mocker.patch("builtins.open", mock_open())
    cube_meta = cube_metadata_generator()(cube_uid)
    mocker.patch("yaml.safe_load", return_value=cube_meta)
    mocker.patch("os.path.exists", return_value=with_params)
    spy = mocker.spy(Cube, "__init__")

    cube_path = os.path.join(cubes_path, cube_uid, config.cube_filename)
    if with_params:
        params_path = os.path.join(cubes_path, cube_uid, config.params_filename)
    else:
        params_path = None

    # Act
    Cube.all(ui)

    # Assert
    spy.assert_called_once_with(ANY, cube_uid, cube_meta, cube_path, params_path)


def test_get_basic_cube_retrieves_metadata_from_comms(
    mocker, comms, basic_body, no_local
):
    # Arrange
    spy = mocker.spy(comms, "get_cube_metadata")

    # Act
    uid = 1
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_called_once_with(uid)


def test_get_basic_cube_retrieves_cube_manifest(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube")

    # Act
    uid = 1
    body = basic_body(uid)
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_called_once_with(body["git_mlcube_url"], uid)


def test_get_basic_cube_doesnt_retrieve_parameters(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_params")

    # Act
    uid = 1
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_not_called()


def test_get_basic_cube_doesnt_retrieve_tarball(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_additional")

    # Act
    uid = 1
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_not_called()


def test_get_cube_with_parameters_retrieves_parameters(
    mocker, comms, params_body, no_local
):
    # Arrange
    spy = mocker.spy(comms, "get_cube_params")

    # Act
    uid = 1
    body = params_body(uid)
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_called_once_with(body["git_parameters_url"], uid)


def test_get_cube_with_tarball_retrieves_tarball(mocker, comms, tar_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_additional")

    # Act
    uid = 1
    body = tar_body(uid)
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_called_once_with(body["tarball_url"], uid)


def test_get_cube_with_tarball_generates_tarball_hash(
    mocker, comms, tar_body, no_local
):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "get_file_sha1")

    # Act
    uid = 1
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_called_once_with(TARBALL_PATH)


def test_get_cube_with_tarball_untars_files(mocker, comms, tar_body, no_local):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "untar")

    # Act
    uid = 1
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_called_once_with(TARBALL_PATH)


def test_get_cube_calls_all(mocker, comms, basic_body):
    # Arrange
    spy = mocker.patch(PATCH_CUBE.format("Cube.all"), return_value=[])

    # Act
    uid = 1
    Cube.get(uid, comms, ui)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("local_cubes", [rand_l(1, 500, 1)])
def test_get_cube_return_local_first(mocker, comms, local_cubes):
    # Arrange
    cube = mocker.create_autospec(spec=Cube)
    uid = local_cubes[0]
    cube.uid = uid
    spy = mocker.patch.object(Cube, "all", return_value=[cube])
    metadata_spy = mocker.patch.object(comms, "get_cube_metadata")

    # Act
    cube = Cube.get(uid, comms, ui)

    # Assert
    assert cube.uid == uid
    spy.assert_called_once()
    metadata_spy.assert_not_called()


@pytest.mark.parametrize("local_cubes", [rand_l(2, 500, 1)])
def test_get_cube_requests_server_if_not_local(mocker, comms, basic_body, local_cubes):
    # Arrange
    cube = mocker.create_autospec(spec=Cube)
    cube.uid = local_cubes[0]
    mocker.patch.object(Cube, "all", return_value=[cube])
    metadata_spy = mocker.patch.object(comms, "get_cube_metadata")

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)

    # Assert
    metadata_spy.assert_called_once()


def test_cube_is_valid_if_no_tarball(mocker, comms, basic_body, no_local):
    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)

    # Assert
    assert cube.is_valid()


def test_cube_is_valid_with_correct_hash(mocker, comms, tar_body, no_local):
    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)

    # Assert
    assert cube.is_valid()


def test_cube_is_invalid_with_incorrect_hash(mocker, comms, tar_body, no_local):
    # Arrange
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value="incorrect_hash")

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)

    # Assert
    assert not cube.is_valid()


@pytest.mark.parametrize("timeout", rand_l(1, 100, 1) + [None])
def test_cube_runs_command_with_pexpect(mocker, ui, comms, basic_body, no_local, timeout):
    # Arrange
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("list_files"), return_value="")
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
    task = "task"
    expected_cmd = f"mlcube run --mlcube={CUBE_PATH} --task={task}"

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)
    cube.run(ui, "task", timeout=timeout)

    # Assert
    spy.assert_called_once_with(expected_cmd, timeout=timeout)


def test_cube_runs_command_with_extra_args(mocker, ui, comms, basic_body, no_local):
    # Arrange
    mpexpect = MockPexpect(0)
    spy = mocker.patch("pexpect.spawn", side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("list_files"), return_value="")
    task = "task"
    expected_cmd = f"mlcube run --mlcube={CUBE_PATH} --task={task} test=test"

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)
    cube.run(ui, task, test="test")

    # Assert
    spy.assert_called_once_with(expected_cmd, timeout=None)


def test_run_stops_execution_if_child_fails(mocker, ui, comms, basic_body, no_local):
    # Arrange
    mpexpect = MockPexpect(1)
    mocker.patch("pexpect.spawn", side_effect=mpexpect.spawn)
    spy = mocker.patch(
        PATCH_CUBE.format("pretty_error"), side_effect=lambda *args, **kwargs: exit()
    )
    task = "task"

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)
    with pytest.raises(SystemExit):
        cube.run(ui, task)

    # Assert
    spy.assert_called_once()


def test_default_output_reads_cube_manifest(mocker, comms, basic_body, no_local):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    spy = mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)
    cube.get_default_output(TASK, OUT_KEY)

    # Assert
    spy.assert_called_once_with(CUBE_PATH, "r")


def test_default_output_returns_specified_path(mocker, comms, basic_body, no_local):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    exp_path = f"./workspace/{VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)
    out_path = cube.get_default_output(TASK, OUT_KEY)

    # Assert
    assert out_path == exp_path


def test_default_output_returns_specified_dict_path(
    mocker, comms, basic_body, no_local
):
    # Arrange
    cube_contents = {
        "tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: {"default": VALUE}}}}}
    }
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    exp_path = f"./workspace/{VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)
    out_path = cube.get_default_output(TASK, OUT_KEY)

    # Assert
    assert out_path == exp_path


def test_default_output_returns_path_with_params(mocker, comms, params_body, no_local):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    params_contents = {PARAM_KEY: PARAM_VALUE}
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents, params_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    exp_path = f"./workspace/{VALUE}/{PARAM_VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid, comms, ui)
    out_path = cube.get_default_output(TASK, OUT_KEY, PARAM_KEY)

    # Assert
    assert out_path == exp_path


@pytest.mark.parametrize("approval", [True, False])
def test_request_registration_approval_returns_users_input(
    mocker, comms, ui, approval, basic_body, no_local
):
    # Arrange
    cube_contents = {
        "tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: {"default": VALUE}}}}}
    }
    mocker.patch("builtins.open", MagicMock())
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    uid = "1"
    mock_benchmark = Benchmark()
    mocker.patch(PATCH_CUBE.format("approval_prompt"), return_value=approval)
    cube = Cube.get(uid, comms, ui)

    # Act
    approved = cube.request_association_approval(mock_benchmark, ui)

    # Assert
    assert approved == approval
