import os
import pytest
from unittest.mock import MagicMock, mock_open, ANY, call

import medperf
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.entities.cube import Cube
from medperf.utils import storage_path
from medperf.tests.utils import cube_local_hashes_generator
from medperf.tests.entities.utils import (
    setup_cube_fs,
    setup_cube_comms,
    setup_cube_comms_downloads,
)
from medperf.tests.mocks.pexpect import MockPexpect
from medperf.tests.mocks.requests import cube_metadata_generator
from medperf.exceptions import (
    ExecutionError,
    InvalidEntityError,
    CommunicationRetrievalError,
)

PATCH_SERVER = "medperf.entities.benchmark.Comms.{}"
PATCH_CUBE = "medperf.entities.cube.{}"
CUBE_PATH = "cube_path"
CUBE_HASH = "cube_hash"
PARAMS_PATH = "params_path"
PARAMS_HASH = "params_hash"
TARBALL_PATH = "additional_files_tarball_path"
TARBALL_HASH = "additional_files_tarball_hash"
IMG_PATH = "image_tarball_url"
IMG_HASH = "image_tarball_hash"

TASK = "task"
OUT_KEY = "out_key"
VALUE = "value"
PARAM_KEY = "param_key"
PARAM_VALUE = "param_value"


@pytest.fixture(
    params={"local": ["1", "2", "3"], "remote": ["4", "5", "6"], "user": ["4"]}
)
def setup(request, mocker, comms, fs):
    local_ents = request.param.get("local", [])
    remote_ents = request.param.get("remote", [])
    user_ents = request.param.get("user", [])
    # Have a list that will contain all uploaded entities of the given type
    uploaded = []

    setup_cube_fs(local_ents, fs)
    setup_cube_comms(mocker, comms, remote_ents, user_ents, uploaded)
    setup_cube_comms_downloads(mocker, comms, fs, remote_ents)
    request.param["uploaded"] = uploaded

    # Mock additional third party elements
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("combine_proc_sp_text"), return_value="")
    mocker.patch(PATCH_CUBE.format("untar"))

    return request.param


@pytest.mark.parametrize("setup", [{"remote": ["63", "237", "17", "3"]}], indirect=True)
def test_get_cube_retrieves_files(mocker, comms, ui, setup):
    # Arrange
    uid = setup["remote"][0]

    # Specify expected path for all downloaded files
    cube_path = os.path.join(storage_path(config.cubes_storage), uid)
    manifest_path = os.path.join(cube_path, config.cube_filename)
    params_path = os.path.join(cube_path, config.workspace_path, config.params_filename)
    add_path = os.path.join(cube_path, config.additional_path, config.tarball_filename)
    img_path = os.path.join(cube_path, config.image_path, "img.tar.gz")
    file_paths = [manifest_path, params_path, add_path, img_path]

    # Act
    Cube.get(uid)

    # Assert
    for file in file_paths:
        assert os.path.exists(file) and os.path.isfile(file)


@pytest.mark.parametrize("setup", [{"remote": ["63", "237", "17", "3"]}], indirect=True)
def test_get_cube_untars_files(mocker, setup):
    # Arrange
    uid = setup["remote"][0]
    spy = mocker.spy(medperf.entities.cube, "untar")
    cube_path = os.path.join(storage_path(config.cubes_storage), uid)
    add_path = os.path.join(cube_path, config.additional_path, config.tarball_filename)
    img_path = os.path.join(cube_path, config.image_path, "img.tar.gz")
    calls = [call(add_path), call(img_path)]

    # Act
    Cube.get(uid)

    # Assert
    spy.assert_has_calls(calls)


@pytest.mark.parametrize("max_attempts", [3, 5, 2])
@pytest.mark.parametrize("setup", [{"remote": ["63", "237", "17", "3"]}], indirect=True)
def test_get_cube_retries_configured_number_of_times(mocker, max_attempts, setup):
    # Arrange
    uid = setup["remote"][0]
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=False)
    mocker.patch(PATCH_CUBE.format("cleanup"))
    spy = mocker.spy(Cube, "download")
    config.cube_get_max_attempts = max_attempts
    calls = [call(ANY)] * max_attempts

    # Act
    with pytest.raises(InvalidEntityError):
        Cube.get(uid)

    # Assert
    spy.assert_has_calls(calls)


@pytest.mark.parametrize(
    "setup",
    [
        {
            "remote": [
                {"id": "63", "parameters_hash": "error"},
                {"id": "237", "parameters_hash": "invalid"},
            ]
        }
    ],
    indirect=True,
)
def test_get_cube_deletes_cube_if_failed(mocker, setup):
    # Arrange
    uid = setup["remote"][0]["id"]
    spy = mocker.patch(PATCH_CUBE.format("cleanup"))
    cube_path = os.path.join(storage_path(config.cubes_storage), str(uid))

    # Act
    with pytest.raises(InvalidEntityError):
        Cube.get(uid)

    # Assert
    spy.assert_called_once_with([cube_path])


def test_get_cube_without_image_configures_mlcube(mocker, comms, basic_body, no_local):
    # Arrange
    # TODO: Need to adapt setup functions so that arbitrary entity configurations are available
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
    expected_cmd = f"mlcube configure --mlcube={CUBE_PATH}"
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), side_effect=[False, True])

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(expected_cmd)


@pytest.mark.parametrize("setup", [{"remote": ["63", "237", "17", "3"]}], indirect=True)
def test_get_cube_with_image_isnt_configured(mocker, setup):
    # Arrange
    uid = setup["remote"][0]
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")

    # Act
    Cube.get(uid)

    # Assert
    spy.assert_not_called()


def test_cube_is_valid_if_no_extrafields(mocker, comms, basic_body):
    # Arrange
    # TODO: Need to adapt setup functions so that arbitrary entity configurations are available
    uid = 1
    local_hashes = cube_local_hashes_generator(with_tarball=False, with_image=False)
    mocker.patch(PATCH_CUBE.format("Cube.get_local_hashes"), return_value=local_hashes)
    cube = mocker.create_autospec(spec=Cube)
    cube.uid = uid
    mocker.patch.object(Cube, "all", return_value=[cube])

    # Act
    cube = Cube.get(uid)

    # Assert
    assert cube.is_valid()


def test_cube_is_invalid_if_invalidated(mocker, ui, comms, basic_body, no_local):
    # Arrange
    uid = 1
    local_hashes = cube_local_hashes_generator()
    mocker.patch(PATCH_CUBE.format("Cube.get_local_hashes"), return_value=local_hashes)
    cube = Cube(cube_metadata_generator()(uid))
    cube.is_cube_valid = False

    # Act & Assert
    assert not cube.is_valid()


def test_cube_is_invalid_with_incorrect_tarball_hash(
    mocker, ui, comms, tar_body, no_local
):
    # Arrange
    uid = 1
    local_hashes = cube_local_hashes_generator(valid=False, with_image=False)
    mocker.patch(PATCH_CUBE.format("Cube.get_local_hashes"), return_value=local_hashes)
    cube = mocker.create_autospec(spec=Cube)
    cube.uid = uid
    mocker.patch.object(Cube, "all", return_value=[cube])

    # Act
    cube = Cube(tar_body(uid))
    is_valid = cube.is_valid()

    # Assert
    assert not is_valid


def test_cube_is_invalid_with_incorrect_image_tarball_hash(
    mocker, comms, img_body, no_local
):
    # Arrange
    local_hashes = cube_local_hashes_generator(valid=False, with_tarball=False)
    mocker.patch(PATCH_CUBE.format("Cube.get_local_hashes"), return_value=local_hashes)

    # Act
    uid = 1
    cube = Cube(img_body(uid))

    # Assert
    assert not cube.is_valid()


@pytest.mark.parametrize("timeout", [847, None])
def test_cube_runs_command_with_pexpect(
    mocker, ui, comms, basic_body, no_local, timeout
):
    # Arrange
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("list_files"), return_value="")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), side_effect=[False, True])
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
    task = "task"
    platform = config.platform
    expected_cmd = (
        f"mlcube run --mlcube={CUBE_PATH} --task={task} --platform={platform}"
    )

    # Act
    uid = 1
    cube = Cube.get(uid)
    cube.run("task", timeout=timeout)

    # Assert
    spy.assert_any_call(expected_cmd, timeout=timeout)


def test_cube_runs_command_with_extra_args(mocker, ui, comms, basic_body, no_local):
    # Arrange
    mpexpect = MockPexpect(0)
    spy = mocker.patch("pexpect.spawn", side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), side_effect=[False, True])
    mocker.patch(PATCH_CUBE.format("list_files"), return_value="")
    task = "task"
    platform = config.platform
    expected_cmd = f'mlcube run --mlcube={CUBE_PATH} --task={task} --platform={platform} test="test"'

    # Act
    uid = 1
    cube = Cube.get(uid)
    cube.run(task, test="test")

    # Assert
    spy.assert_any_call(expected_cmd, timeout=None)


def test_run_stops_execution_if_child_fails(mocker, ui, comms, basic_body, no_local):
    # Arrange
    mpexpect = MockPexpect(1)
    mocker.patch("pexpect.spawn", side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
    task = "task"

    # Act & Assert
    uid = 1
    cube = Cube.get(uid)
    with pytest.raises(ExecutionError):
        cube.run(task)


def test_default_output_reads_cube_manifest(mocker, comms, basic_body, no_local):
    # Arrange
    # TODO: allow passing contents to mocked files
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    spy = mocker.patch("builtins.open", MagicMock())
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), side_effect=[False, True])
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    # Act
    uid = 1
    cube = Cube.get(uid)
    cube.get_default_output(TASK, OUT_KEY)

    # Assert
    spy.assert_called_once_with(CUBE_PATH, "r")


def test_default_output_returns_specified_path(mocker, comms, basic_body, no_local):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    mocker.patch("builtins.open", MagicMock())
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), side_effect=[False, True])
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    exp_path = f"./workspace/{VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid)
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
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), side_effect=[False, True])
    m = MagicMock(side_effect=[cube_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    exp_path = f"./workspace/{VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid)
    out_path = cube.get_default_output(TASK, OUT_KEY)

    # Assert
    assert out_path == exp_path


def test_default_output_returns_path_with_params(mocker, comms, params_body, no_local):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    params_contents = {PARAM_KEY: PARAM_VALUE}
    mocker.patch("builtins.open", MagicMock())
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), side_effect=[False, True])
    m = MagicMock(side_effect=[cube_contents, params_contents])
    mocker.patch(PATCH_CUBE.format("yaml.safe_load"), m)

    exp_path = f"./workspace/{VALUE}/{PARAM_VALUE}"

    # Act
    uid = 1
    cube = Cube.get(uid)
    out_path = cube.get_default_output(TASK, OUT_KEY, PARAM_KEY)

    # Assert
    assert out_path == exp_path


@pytest.mark.parametrize("cube_uid", [73, 9])
@pytest.mark.parametrize("is_valid", [True, False])
@pytest.mark.parametrize("with_tarball", [True, False])
@pytest.mark.parametrize("with_image", [True, False])
def test_local_cubes_validity_can_be_detected(
    mocker, cube_uid, is_valid, with_tarball, with_image, comms, ui
):
    # Arrange
    if not any([is_valid, with_tarball, with_image]):
        # an outlier test parameters combination
        return
    cube_uid = str(cube_uid)
    fs = iter([(".", (cube_uid,), ())])
    mocker.patch("os.walk", return_value=fs)
    mocker.patch("builtins.open", mock_open())
    cube_meta = cube_metadata_generator(False, with_tarball, with_image)(cube_uid)
    cube_local_hashes = cube_local_hashes_generator(is_valid, with_tarball, with_image)
    mocker.patch.object(comms, "get_cubes", side_effect=CommunicationRetrievalError)
    mocker.patch("yaml.safe_load", side_effect=[cube_meta, cube_local_hashes])
    mocker.patch("os.path.exists")

    # Act
    local_cube = Cube.all()[0]
    is_cube_valid = local_cube.is_valid()

    # Assert
    assert is_cube_valid == is_valid


def test_download_saves_local_hashes(mocker, comms, basic_body, no_local):
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
    cube = Cube.get(1)
    spy = mocker.patch(PATCH_CUBE.format("Cube.store_local_hashes"))
    # Act
    cube.download()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("precalculated", [False, True])
def test_download_does_not_ignore_hashes_if_precalculated(
    mocker, ui, comms, precalculated
):
    # Arrange
    meta = cube_metadata_generator(with_tarball=True, with_image=True)(1)
    if not precalculated:
        meta["additional_files_tarball_hash"] = ""
        meta["image_tarball_hash"] = ""

    cube = Cube(meta)
    mocker.patch(PATCH_CUBE.format("Cube.store_local_hashes"))
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value="some_local_hash")
    # Act
    cube.download()

    # Assert
    if precalculated:
        assert cube.additional_hash == meta["additional_files_tarball_hash"]
        assert cube.image_tarball_hash == meta["image_tarball_hash"]
    else:
        assert cube.additional_hash == "some_local_hash"
        assert cube.image_tarball_hash == "some_local_hash"
