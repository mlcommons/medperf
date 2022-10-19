import os
import pytest
from unittest.mock import MagicMock, mock_open, ANY, call

import medperf
from medperf.ui.interface import UI
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
PARAMS_PATH = "params_path"
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
    mocker.patch.object(comms, "get_cube_image", return_value=IMG_PATH)
    mocker.patch(PATCH_CUBE.format("untar"))
    mocker.patch(PATCH_CUBE.format("save_cube_metadata"))
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
    return body_gen


@pytest.fixture
def params_body(mocker, comms):
    body_gen = cube_metadata_generator(with_params=True)
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("combine_proc_sp_text"), return_value="")
    return body_gen


@pytest.fixture
def tar_body(mocker, comms):
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value=TARBALL_HASH)
    body_gen = cube_metadata_generator(with_tarball=True)
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
    mpexpect = MockPexpect(0)
    mocker.patch(PATCH_CUBE.format("pexpect.spawn"), side_effect=mpexpect.spawn)
    mocker.patch(PATCH_CUBE.format("combine_proc_sp_text"), return_value="")
    return body_gen


@pytest.fixture
def img_body(mocker, comms):
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value=IMG_HASH)
    body_gen = cube_metadata_generator(with_image=True)
    mocker.patch.object(comms, "get_cube_metadata", side_effect=body_gen)
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
    hashes_path = os.path.join(cubes_path, cube_uid, config.cube_hashes_filename)

    # Act
    Cube.all()

    # Assert
    spy.assert_has_calls([call(meta_path, "r"), call(hashes_path, "r")])
    assert spy.call_count == 2


@pytest.mark.parametrize("cube_uid", [387, 1, 6])
@pytest.mark.parametrize("with_params", [True, False])
def test_all_creates_cube_with_expected_content(mocker, cube_uid, with_params):
    # Arrange
    cube_uid = str(cube_uid)
    cubes_path = storage_path(config.cubes_storage)
    fs = iter([(".", (cube_uid,), ())])
    mocker.patch("os.walk", return_value=fs)
    mocker.patch("builtins.open", mock_open())
    cube_meta = cube_metadata_generator()(cube_uid)
    cube_local_hashes = cube_local_hashes_generator()
    mocker.patch("yaml.safe_load", side_effect=[cube_meta, cube_local_hashes])
    mocker.patch("os.path.exists", return_value=with_params)
    spy = mocker.spy(Cube, "__init__")

    cube_path = os.path.join(cubes_path, cube_uid, config.cube_filename)
    if with_params:
        params_path = os.path.join(cubes_path, cube_uid, config.params_filename)
    else:
        params_path = None

    # Act
    Cube.all()

    # Assert
    spy.assert_called_once_with(
        ANY,
        cube_uid,
        cube_meta,
        cube_path,
        params_path,
        cube_local_hashes["additional_files_tarball_hash"],
        cube_local_hashes["image_tarball_hash"],
    )


def test_get_basic_cube_retrieves_metadata_from_comms(
    mocker, comms, basic_body, no_local
):
    # Arrange
    spy = mocker.spy(comms, "get_cube_metadata")

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(uid)


def test_get_basic_cube_retrieves_cube_manifest(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube")

    # Act
    uid = 1
    body = basic_body(uid)
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(body["git_mlcube_url"], uid)


def test_get_basic_cube_doesnt_retrieve_parameters(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_params")

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

    # Act
    uid = 1
    body = params_body(uid)
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(body["git_parameters_url"], uid)


def test_get_cube_with_tarball_retrieves_tarball(mocker, comms, tar_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_additional")

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

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(TARBALL_PATH)


def test_get_cube_with_tarball_untars_files(mocker, comms, tar_body, no_local):
    # Arrange
    spy = mocker.spy(medperf.entities.cube, "untar")

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(TARBALL_PATH)


def test_get_cube_calls_all(mocker, comms, basic_body):
    # Arrange
    spy = mocker.patch(PATCH_CUBE.format("Cube.all"), return_value=[])

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

    # Act
    uid = 1
    cube = Cube.get(uid)

    # Assert
    metadata_spy.assert_called_once()


def test_get_cube_with_image_retrieves_image(mocker, comms, img_body, no_local):
    # Arrange
    spy = mocker.spy(comms, "get_cube_image")

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

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(IMG_PATH)


def test_get_cube_with_image_untars_image(mocker, comms, img_body, no_local):
    # Arragen
    spy = mocker.spy(medperf.entities.cube, "untar")

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(IMG_PATH)


def test_get_cube_without_image_configures_mlcube(mocker, comms, basic_body, no_local):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")
    expected_cmd = f"mlcube configure --mlcube={CUBE_PATH}"

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_called_once_with(expected_cmd)


def test_get_cube_with_image_isnt_configured(mocker, comms, img_body, no_local):
    # Arrange
    spy = mocker.spy(medperf.entities.cube.pexpect, "spawn")

    # Act
    uid = 1
    Cube.get(uid)

    # Assert
    spy.assert_not_called()


def test_cube_is_valid_if_no_extrafields(mocker, comms, basic_body, no_local):
    # Act
    uid = 1
    cube = Cube.get(uid)

    # Assert
    assert cube.is_valid()


def test_cube_is_valid_with_correct_tarball_hash(mocker, comms, tar_body, no_local):
    # Act
    uid = 1
    cube = Cube.get(uid)

    # Assert
    assert cube.is_valid()


def test_cube_is_valid_with_correct_image_tarball_hash(
    mocker, comms, img_body, no_local
):
    # Act
    uid = 1
    cube = Cube.get(uid)

    # Assert
    assert cube.is_valid()


def test_cube_is_invalid_if_invalidated(mocker, ui, comms, basic_body, no_local):
    # Arrange
    uid = 1
    cube = Cube.get(uid)
    cube.meta["is_valid"] = False

    # Act & Assert
    assert not cube.is_valid()


def test_cube_is_invalid_with_incorrect_tarball_hash(
    mocker, ui, comms, tar_body, no_local
):
    # Arrange
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value="incorrect_hash")

    # Act
    uid = 1
    cube = Cube.get(uid)

    # Assert
    assert not cube.is_valid()


def test_cube_is_invalid_with_incorrect_image_tarball_hash(
    mocker, comms, img_body, no_local
):
    # Arrange
    mocker.patch(PATCH_CUBE.format("get_file_sha1"), return_value="incorrect_hash")

    # Act
    uid = 1
    cube = Cube.get(uid)

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
@pytest.mark.parametrize("with_tarball", [True, False])
@pytest.mark.parametrize("with_image", [True, False])
def test_get_cube_saves_cube_metadata(
    mocker, comms, no_local, cube_uid, with_tarball, with_image
):
    # Arrange
    meta = cube_metadata_generator(False, with_tarball, with_image)(cube_uid)
    local_hashes = cube_local_hashes_generator(True, with_tarball, with_image)

    mocker.patch.object(comms, "get_cube_metadata", return_value=meta)
    hashes_list = []
    if with_tarball:
        hashes_list.append(local_hashes[TARBALL_HASH])
    if with_image:
        hashes_list.append(local_hashes[IMG_HASH])

    mocker.patch(PATCH_CUBE.format("get_file_sha1"), side_effect=hashes_list)
    spy = mocker.patch(PATCH_CUBE.format("save_cube_metadata"))

    # Act
    Cube.get(cube_uid)

    # Assert
    spy.assert_called_once_with(meta, local_hashes)


def test_todict_returns_expected_dict(mocker, basic_body, no_local):
    # Arrange
    cube = Cube.get(1)
    exp_body = basic_body(1)

    # Act
    data = cube.todict()

    # Assert
    assert data == exp_body


def test_upload_runs_comms_upload_proc(mocker, comms, basic_body, no_local):
    # Arrange
    cube = Cube.get(1)
    spy = mocker.patch.object(comms, "upload_mlcube")

    # Act
    cube.upload()

    # Assert
    spy.assert_called_once_with(cube.todict())


@pytest.mark.parametrize("uid", [48, 272, 478])
def test_upload_returns_comms_generated_uid(mocker, comms, basic_body, no_local, uid):
    # Arrange
    cube = Cube.get(1)
    mocker.patch.object(comms, "upload_mlcube", return_value=uid)

    # Act
    returned_uid = cube.upload()

    # Assert
    assert uid == returned_uid
