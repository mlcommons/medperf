import os
import pytest
from unittest.mock import MagicMock, mock_open, ANY, call

import medperf
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.entities.cube import Cube
from medperf.utils import storage_path
from medperf.tests.utils import cube_local_hashes_generator
from medperf.tests.mocks.pexpect import MockPexpect
from medperf.tests.mocks.requests import cube_metadata_generator

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


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    mocker.patch.object(comms, "get_cube", return_value=CUBE_PATH)
    mocker.patch.object(comms, "get_cube_params", return_value=PARAMS_PATH)
    mocker.patch.object(comms, "get_cube_additional", return_value=TARBALL_PATH)
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value=TARBALL_HASH)
    mocker.patch.object(comms, "get_cube_image", return_value=IMG_PATH)
    mocker.patch(PATCH_CUBE.format("untar"))
    config.comms = comms
    return comms


@pytest.fixture
def no_local(mocker):
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("combine_proc_sp_text"), return_value="")
    mocker.patch(PATCH_CUBE.format("Cube.all"), return_value=[])


@pytest.fixture
def basic_body(mocker, comms):
    body_gen = cube_metadata_generator()
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("combine_proc_sp_text"), return_value="")
    mocker.patch(PATCH_CUBE.format("Cube.store_local_hashes"))
    mocker.patch(PATCH_CUBE.format("Cube.write"))
    return body_gen


@pytest.fixture
def params_body(mocker, comms):
    mocker.patch(
        PATCH_CUBE.format("get_file_sha1"), side_effect=[CUBE_HASH, PARAMS_HASH]
    )
    body_gen = cube_metadata_generator(with_params=True)
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("combine_proc_sp_text"), return_value="")
    mocker.patch(PATCH_CUBE.format("Cube.store_local_hashes"))
    mocker.patch(PATCH_CUBE.format("Cube.write"))
    return body_gen


@pytest.fixture
def tar_body(mocker, comms):
    mocker.patch(
        PATCH_CUBE.format("get_file_sha1"), side_effect=[CUBE_HASH, TARBALL_HASH]
    )
    body_gen = cube_metadata_generator(with_tarball=True)
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("combine_proc_sp_text"), return_value="")
    mocker.patch(PATCH_CUBE.format("Cube.store_local_hashes"))
    mocker.patch(PATCH_CUBE.format("Cube.write"))
    return body_gen


@pytest.fixture
def img_body(mocker, comms):
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), side_effect=[CUBE_HASH, IMG_HASH])
    body_gen = cube_metadata_generator(with_image=True)
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    mocker.patch(PATCH_CUBE.format("Cube.store_local_hashes"))
    mocker.patch(PATCH_CUBE.format("Cube.write"))
    return body_gen


def test_all_looks_for_cubes_in_correct_path(mocker):
    # Arrange
    cubes_path = storage_path(config.cubes_storage)
    fs = iter([(".", (), ())])
    spy = mocker.patch("os.walk", return_value=fs)

    # Act
    Cube.all()

    # Assert
    spy.assert_called_once_with(cubes_path)


@pytest.mark.parametrize("cube_uid", [40, 426, 418])
def test_all_reads_local_cube_metadata(mocker, cube_uid):
    # Arrange
    cube_uid = str(cube_uid)
    cubes_path = storage_path(config.cubes_storage)
    fs = iter([(".", (cube_uid,), ())])
    mocker.patch("os.walk", return_value=fs)
    spy = mocker.patch("builtins.open", return_value=mock_open().return_value)
    cube_meta = cube_metadata_generator()(cube_uid)
    mocker.patch("yaml.safe_load", return_value=cube_meta)

    meta_path = os.path.join(cubes_path, cube_uid, config.cube_metadata_filename)

    # Act
    Cube.all()

    # Assert
    spy.assert_called_once_with(meta_path, "r")


@pytest.mark.parametrize("cube_uid", [387, 1, 6])
def test_all_creates_cube_with_expected_content(mocker, cube_uid):
    # Arrange
    cube_uid = str(cube_uid)
    fs = iter([(".", (cube_uid,), ())])
    mocker.patch("os.walk", return_value=fs)
    mocker.patch("builtins.open", mock_open())
    cube_meta = cube_metadata_generator()(cube_uid)
    mocker.patch(
        PATCH_CUBE.format("Cube._Cube__get_local_dict"), return_value=cube_meta
    )
    spy = mocker.spy(Cube, "__init__")

    # Act
    Cube.all()

    # Assert
    spy.assert_called_once_with(ANY, cube_meta)


def test_get_basic_cube_retrieves_metadata_from_comms(
    mocker, comms, basic_body, no_local
):
    # Arrange
    spy = mocker.spy(comms, "get_cube_metadata")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(uid)


def test_get_basic_cube_retrieves_cube_manifest(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    body = basic_body(uid)
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(body["git_mlcube_url"], uid)


def test_get_basic_cube_doesnt_retrieve_parameters(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_params")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_not_called()


@pytest.mark.parametrize("server_call", ["get_cube_additional", "get_cube_image"])
def test_get_basic_cube_doesnt_retrieve_extra_fields(
    mocker, comms, basic_body, no_local, server_call
):
    # Arrange
    spy = mocker.spy(comms, server_call)
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_not_called()


def test_get_cube_with_parameters_retrieves_parameters(
    mocker, comms, params_body, no_local
):
    # Arrange
    spy = mocker.spy(comms, "get_cube_params")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    body = params_body(uid)
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(body["git_parameters_url"], uid)


def test_get_cube_with_tarball_retrieves_tarball(mocker, comms, tar_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_additional")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    body = tar_body(uid)
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(body["additional_files_tarball_url"], uid)


def test_get_cube_with_tarball_generates_tarball_hash(
    mocker, comms, tar_body, no_local
):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "get_file_sha1")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_has_calls([call(CUBE_PATH), call(TARBALL_PATH)])


def test_get_cube_with_tarball_untars_files(mocker, comms, tar_body, no_local):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "untar")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(TARBALL_PATH)


def test_get_cube_calls_all(mocker, comms, basic_body):
    # Arrange
    spy = mocker.patch(PATCH_CUBE.format("Cube.all"), return_value=[])
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("local_cubes", [[32, 87, 9]])
def test_get_cube_return_local_first(mocker, comms, local_cubes):
    # Arrange
    cube = mocker.create_autospec(spec=Cube)
    uid = local_cubes[0]
    cube.uid = uid
    spy = mocker.patch.object(Cube, "all", return_value=[cube])
    metadata_spy = mocker.patch.object(comms, "get_cube_metadata")

    # Act
    cube = Cube.get(uid)

    # Assert
    assert cube.uid == uid
    spy.assert_called_once()
    metadata_spy.assert_not_called()


def test_get_cube_requests_server_if_not_local(mocker, comms, basic_body):
    # Arrange
    cube = mocker.create_autospec(spec=Cube)
    cube.uid = "2"
    mocker.patch.object(Cube, "all", return_value=[cube])
    metadata_spy = mocker.patch.object(comms, "get_cube_metadata")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    cube = Cube.get(uid)

    # Assert
    metadata_spy.assert_called_once()


def test_get_cube_with_image_retrieves_image(mocker, comms, img_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_image")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    body = img_body(uid)
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(body["image_tarball_url"], uid)


def test_get_cube_with_image_generates_image_tarball_hash(
    mocker, comms, img_body, no_local
):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "get_file_sha1")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_has_calls([call(CUBE_PATH), call(IMG_PATH)])


def test_get_cube_with_image_untars_image(mocker, comms, img_body, no_local):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "untar")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(IMG_PATH)


def test_get_cube_checks_validity(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("max_attempts", [3, 5, 2])
def test_get_cube_retries_configured_number_of_times(
    mocker, comms, basic_body, no_local, max_attempts
):
    # Arrange
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=False)
    mocker.patch(PATCH_CUBE.format("cleanup"))
    err_spy = mocker.patch(PATCH_CUBE.format("pretty_error"))
    spy = mocker.patch(PATCH_CUBE.format("Cube.download"))
    config.cube_get_max_attempts = max_attempts
    calls = [call()] * max_attempts

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_has_calls(calls)
    err_spy.assert_called_once()


@pytest.mark.parametrize("uid", [3, 75, 918])
def test_get_cube_deletes_cube_if_failed(mocker, comms, basic_body, no_local, uid):
    # Arrange
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=False)
    spy = mocker.patch(PATCH_CUBE.format("cleanup"))
    err_spy = mocker.patch(PATCH_CUBE.format("pretty_error"))
    cube_path = os.path.join(storage_path(config.cubes_storage), str(uid))

    # Act
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with([cube_path])
    err_spy.assert_called_once()


def test_get_cube_raises_error_if_failed(mocker, comms, basic_body, no_local):
    # Arrange
    uid = 1
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=False)
    mocker.patch(PATCH_CUBE.format("cleanup"))
    err_spy = mocker.patch(PATCH_CUBE.format("pretty_error"))

    # Act
    Cube.get(uid)

    # Assert
    err_spy.assert_called_once()


def test_get_cube_without_image_configures_mlcube(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
    expected_cmd = f"mlcube configure --mlcube={CUBE_PATH}"
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(expected_cmd)


def test_get_cube_with_image_isnt_configured(mocker, comms, img_body, no_local):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_not_called()


def test_cube_is_valid_if_no_extrafields(mocker, comms, basic_body):
    # Arrange
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


def test_cube_is_valid_with_correct_tarball_hash(mocker, comms, tar_body, no_local):
    # Arrange
    uid = 1
    local_hashes = cube_local_hashes_generator(with_image=False)
    mocker.patch(PATCH_CUBE.format("Cube.get_local_hashes"), return_value=local_hashes)

    # Act
    cube = Cube.get(uid)

    # Assert
    assert cube.is_valid()


def test_cube_is_valid_with_correct_image_tarball_hash(
    mocker, comms, img_body, no_local
):
    # Arange
    uid = 1
    local_hashes = cube_local_hashes_generator(with_tarball=False)
    mocker.patch(PATCH_CUBE.format("Cube.get_local_hashes"), return_value=local_hashes)

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
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
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
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
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
    with pytest.raises(RuntimeError):
        cube.run(task)


def test_default_output_reads_cube_manifest(mocker, comms, basic_body, no_local):
    # Arrange
    cube_contents = {"tasks": {TASK: {"parameters": {"outputs": {OUT_KEY: VALUE}}}}}
    spy = mocker.patch("builtins.open", MagicMock())
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
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
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
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
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
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
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
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
    mocker, cube_uid, is_valid, with_tarball, with_image
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
    mocker.patch("yaml.safe_load", side_effect=[cube_meta, cube_local_hashes])
    mocker.patch("os.path.exists")

    # Act
    local_cube = Cube.all()[0]
    is_cube_valid = local_cube.is_valid()

    # Assert
    assert is_cube_valid == is_valid


@pytest.mark.parametrize("cube_uid", [269, 90, 374])
def test_get_downloads_and_writes_cube(mocker, comms, no_local, cube_uid):
    # Arrange
    meta = cube_metadata_generator()(cube_uid)

    mocker.patch.object(comms, "get_cube_metadata", return_value=meta)
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
    down_spy = mocker.patch(PATCH_CUBE.format("Cube.download"))
    write_spy = mocker.patch(PATCH_CUBE.format("Cube.write"))

    # Act
    Cube.get(cube_uid)

    # Assert
    down_spy.assert_called_once()
    write_spy.assert_called_once()


def test_todict_returns_expected_dict(mocker, basic_body, no_local):
    # Arrange
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
    cube = Cube.get(1)
    exp_body = basic_body(1)

    # Act
    data = cube.todict()

    # Assert
    assert data == exp_body


def test_upload_runs_comms_upload_proc(mocker, comms, basic_body, no_local):
    # Arrange
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
    spy = mocker.patch.object(comms, "upload_mlcube")
    cube = Cube.get(1)

    # Act
    cube.upload()

    # Assert
    spy.assert_called_once_with(cube.todict())


def test_upload_returns_comms_generated_body(mocker, comms, basic_body, no_local):
    # Arrange
    mocker.patch(PATCH_CUBE.format("Cube.is_valid"), return_value=True)
    cube = Cube.get(1)
    body = cube_metadata_generator()(1)
    mocker.patch.object(comms, "upload_mlcube", return_value=body)

    # Act
    returned_body = cube.upload()

    # Assert
    assert body == returned_body


def test_is_valid_reads_local_hashes(mocker, comms, basic_body, no_local):
    # Arrange
    cube = Cube(basic_body(1))
    local_hashes = cube_local_hashes_generator()
    spy = mocker.patch(
        PATCH_CUBE.format("Cube.get_local_hashes"), return_value=local_hashes
    )
    # Act
    cube.is_valid()

    # Assert
    spy.assert_called_once()


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


@pytest.mark.parametrize("cube_uid", [269, 90, 374])
def test_write_writes_to_expected_path(mocker, cube_uid):
    # Arrange
    meta = cube_metadata_generator()(cube_uid)
    open_spy = mocker.patch("builtins.open", mock_open())
    yaml_spy = mocker.patch("yaml.dump")
    mocker.patch(PATCH_CUBE.format("os.makedirs"))
    exp_file = os.path.join(
        storage_path(config.cubes_storage), str(cube_uid), config.cube_metadata_filename
    )

    # Act
    cube = Cube(meta)
    cube.write()

    # Assert
    open_spy.assert_called_once_with(exp_file, "w")
    yaml_spy.assert_called_once_with(cube.todict(), ANY)
