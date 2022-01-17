from unittest.mock import MagicMock, mock_open, call, ANY
from pathlib import Path
import datetime as dt
import time_machine
import random
import pytest
import os

from medperf import utils
from medperf.ui import UI
from medperf.config import config
from medperf.tests.utils import rand_l
from medperf.tests.mocks import MockCube, MockTar


parent = config["storage"]
data = config["data_storage"]
cubes = config["cubes_storage"]
results = config["results_storage"]
tmp = config["tmp_storage"]
config_dirs = [parent, data, cubes, results, tmp]
patch_utils = "medperf.utils.{}"


def init_mock_isdir(existing_dirs):
    def isdir(dir):
        return dir in existing_dirs

    return isdir


@pytest.fixture
def datasets(request):
    size = request.param
    uids = rand_l(1, 5000, size)
    uids = [str(x) for x in uids]
    for i in range(size):
        if random.randint(0, 1):
            uids[i] = config["tmp_reg_prefix"] + uids[i]

    return uids


@pytest.fixture
def dict_with_nones(request):
    num_keys = request.param
    keys = rand_l(1, 5000, num_keys)
    vals = [random.choice([None, x]) for x in keys]
    return {k: v for k, v in zip(keys, vals)}


@pytest.fixture
def ui(mocker):
    ui = mocker.create_autospec(spec=UI)
    return ui


@pytest.fixture
def filesystem():
    fs = iter([("/foo", ("bar",), ("baz",)), ("/foo/bar", (), ("spam", "eggs")),])
    files = ["/foo/baz", "/foo/bar/spam", "/foo/bar/eggs"]
    return [fs, files]


@pytest.mark.parametrize("file", ["./test.txt", "../file.yaml", "folder/file.zip"])
def test_get_file_sha1_opens_specified_file(mocker, file):
    # Arrange
    spy = mocker.patch("builtins.open", mock_open())

    # Act
    utils.get_file_sha1(file)

    # Assert
    spy.assert_called_once_with(file, "rb")


@pytest.mark.parametrize(
    "file_io",
    [
        (b"test file\n", "0181d93fee60b818e3f92e470ea97a2aff4ca56a"),
        (b"file\nwith\nmultilines\n", "a69ce122f95a94dc02485764d463b10545a558c8"),
    ],
)
def test_get_file_sha1_calculates_hash(mocker, file_io):
    # Arrange
    file_contents, expected_hash = file_io
    mocker.patch("builtins.open", mock_open(read_data=file_contents))

    # Act
    hash = utils.get_file_sha1("")

    # Assert
    assert hash == expected_hash


@pytest.mark.parametrize(
    "existing_dirs",
    [
        random.sample(config_dirs, random.randint(0, len(config_dirs)))
        for _ in range(20)
    ],
)
def test_init_storage_creates_nonexisting_paths(mocker, existing_dirs):
    # Arrange
    mock_isdir = init_mock_isdir(existing_dirs)
    mocker.patch("os.path.isdir", side_effect=mock_isdir)
    spy = mocker.patch("os.mkdir")
    exp_mkdirs = list(set(config_dirs) - set(existing_dirs))
    exp_calls = [call(exp_mkdir) for exp_mkdir in exp_mkdirs]

    # Act
    utils.init_storage()

    # Assert
    spy.assert_has_calls(exp_calls, any_order=True)


def test_cleanup_removes_temporary_storage(mocker):
    # Arrange
    mocker.patch("os.path.exists", return_value=True)
    spy = mocker.patch(patch_utils.format("rmtree"))
    mocker.patch(patch_utils.format("get_dsets"), return_value=[])

    # Act
    utils.cleanup()

    # Assert
    spy.assert_called_once_with(tmp, ignore_errors=True)


@pytest.mark.parametrize("datasets", rand_l(1, 1000, 5), indirect=True)
def test_cleanup_removes_only_invalid_datasets(mocker, datasets):
    # Arrange
    prefix = config["tmp_reg_prefix"]
    # Mock that the temporary storage path doesn't exist
    mocker.patch("os.path.exists", side_effect=lambda x: x != tmp)
    mocker.patch(patch_utils.format("get_dsets"), return_value=datasets)
    spy = mocker.patch(patch_utils.format("rmtree"))

    invalid_dsets = [dset for dset in datasets if dset.startswith(prefix)]
    invalid_dsets = [os.path.join(data, dset) for dset in invalid_dsets]
    exp_calls = [call(inv_dset, ignore_errors=True) for inv_dset in invalid_dsets]

    # Act
    utils.cleanup()

    # Assert
    spy.assert_has_calls(exp_calls, any_order=True)
    # Account for the tmp_storage call
    assert spy.call_count == len(exp_calls)


@pytest.mark.parametrize("datasets", rand_l(1, 1000, 5), indirect=True)
def test_get_dsets_returns_uids_of_datasets(mocker, datasets):
    # Arrange
    mock_walk_return = iter([(data, datasets, ())])
    mocker.patch("os.walk", return_value=mock_walk_return)

    # Act
    dsets = utils.get_dsets()

    # Assert
    assert dsets == datasets


@pytest.mark.parametrize("msg", ["test", "error message", "can't find cube"])
def test_pretty_error_displays_message(mocker, ui, msg):
    # Arrange
    spy = mocker.patch.object(ui, "print_error")
    mocker.patch(patch_utils.format("cleanup"))
    mocker.patch(patch_utils.format("exit"))

    # Act
    utils.pretty_error(msg, ui)

    # Assert
    printed_msg = spy.call_args_list[0][0][0]
    assert msg in printed_msg


@pytest.mark.parametrize("clean", [True, False])
def test_pretty_error_runs_cleanup_when_requested(mocker, ui, clean):
    # Arrange
    spy = mocker.patch(patch_utils.format("cleanup"))
    mocker.patch("typer.echo")
    mocker.patch(patch_utils.format("exit"))

    # Act
    utils.pretty_error("test", ui, clean)

    # Assert
    if clean:
        spy.assert_called_once()
    else:
        spy.assert_not_called()


def test_pretty_error_exits_program(mocker, ui):
    # Arrange
    mocker.patch(patch_utils.format("cleanup"))
    mocker.patch("typer.echo")
    spy = mocker.patch(patch_utils.format("exit"))

    # Act
    utils.pretty_error("test", ui)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("timeparams", [(2000, 10, 23), (2021, 1, 2), (2012, 5, 24)])
def test_generate_tmp_datapath_creates_expected_path(mocker, timeparams):
    # Arrange
    datetime = dt.datetime(*timeparams)
    traveller = time_machine.travel(datetime)
    traveller.start()
    timestamp = dt.datetime.timestamp(datetime)
    mocker.patch("os.path.isdir", return_value=False)
    spy = mocker.patch("os.makedirs")
    tmp_path = f"{config['tmp_reg_prefix']}{int(timestamp)}"
    exp_out_path = os.path.join(data, tmp_path, "data")

    # Act
    utils.generate_tmp_datapath()

    # Assert
    spy.assert_called_once_with(exp_out_path)
    traveller.stop()


@pytest.mark.parametrize("is_valid", [True, False])
def test_cube_validity_fails_when_invalid(mocker, ui, is_valid):
    # Arrange
    spy = mocker.patch(patch_utils.format("pretty_error"))
    cube = MockCube(is_valid)

    # Act
    utils.check_cube_validity(cube, ui)

    # Assert
    if not is_valid:
        spy.assert_called_once()
    else:
        spy.assert_not_called()


@pytest.mark.parametrize("file", ["test.tar.bz", "path/to/file.tar.bz"])
def test_untar_additional_opens_specified_file(mocker, file):
    # Arrange
    spy = mocker.patch("tarfile.open")
    mocker.patch("tarfile.TarFile.extractall")
    mocker.patch("tarfile.TarFile.close")
    mocker.patch("os.remove")

    # Act
    utils.untar_additional(file)

    # Assert
    spy.assert_called_once_with(file)


@pytest.mark.parametrize("file", ["./test.tar.bz", "path/to/file.tar.bz"])
def test_untar_additional_extracts_to_parent_directory(mocker, file):
    # Arrange
    parent_path = str(Path(file).parent)
    mocker.patch("tarfile.open", return_value=MockTar())
    spy = mocker.spy(MockTar, "extractall")
    mocker.patch("os.remove")

    # Act
    utils.untar_additional(file)

    # Assert
    spy.assert_called_once_with(ANY, parent_path)


@pytest.mark.parametrize("file", ["./test.tar.bz", "path/to/file.tar.bz"])
def test_untar_additional_removes_tarfile(mocker, file):
    # Arrange
    mocker.patch("tarfile.open")
    mocker.patch("tarfile.TarFile.extractall")
    mocker.patch("tarfile.TarFile.close")
    spy = mocker.patch("os.remove")

    # Act
    utils.untar_additional(file)

    # Assert
    spy.assert_called_once_with(file)


def test_approval_prompt_asks_for_user_input(mocker, ui):
    # Arrange
    spy = mocker.patch.object(ui, "prompt", return_value="y")

    # Act
    utils.approval_prompt("test", ui)

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize(
    "inputted_strs",
    [
        (["y"], 1),
        (["test", "what", "Y"], 3),
        (["this", "is", "a", "test", "n", "for", "approval"], 5),
        (["N", "y"], 1),
        (["No", "y"], 2),
    ],
)
def test_approval_prompt_repeats_until_valid_answer(mocker, ui, inputted_strs):
    # Arrange
    str_list = inputted_strs[0]
    exp_repeats = inputted_strs[1]
    spy = mocker.patch.object(ui, "prompt", side_effect=str_list)

    # Act
    utils.approval_prompt("test prompt", ui)

    # Assert
    spy.call_count == exp_repeats


@pytest.mark.parametrize("input_val", random.choices("YyNn", k=6))
def test_approval_prompt_returns_approved_boolean(mocker, ui, input_val):
    # Arrange
    mocker.patch.object(ui, "prompt", return_value=input_val)

    # Act
    approved = utils.approval_prompt("test approval return", ui)

    # Assert
    assert approved == (input_val in "yY")


@pytest.mark.parametrize("dict_with_nones", rand_l(0, 100, 5), indirect=True)
def test_dict_pretty_print_passes_clean_dict_to_yaml(mocker, ui, dict_with_nones):
    # Arrange
    mocker.patch("typer.echo")
    spy = mocker.patch("yaml.dump", return_value="")
    exp_dict = {k: v for k, v in dict_with_nones.items() if v is not None}

    # Act
    utils.dict_pretty_print(dict_with_nones, ui)

    # Assert
    spy.assert_called_once_with(exp_dict)


def test_get_folder_sha1_hashes_all_files_in_folder(mocker, filesystem):
    # Arrange
    fs = filesystem[0]
    files = filesystem[1]
    exp_calls = [call(file) for file in files]
    mocker.patch("os.walk", return_value=fs)
    spy = mocker.patch(patch_utils.format("get_file_sha1"), side_effect=files)

    # Act
    utils.get_folder_sha1("test")

    # Assert
    spy.assert_has_calls(exp_calls)


def test_get_folder_sha1_sorts_individual_hashes(mocker, filesystem):
    # Arrange
    fs = filesystem[0]
    files = filesystem[1]
    mocker.patch("os.walk", return_value=fs)
    mocker.patch(patch_utils.format("get_file_sha1"), side_effect=files)
    spy = mocker.patch("builtins.sorted", side_effect=sorted)

    # Act
    utils.get_folder_sha1("test")

    # Assert
    spy.assert_called_once_with(files)


def test_get_folder_sha1_returns_expected_hash(mocker, filesystem):
    # Arrange
    fs = filesystem[0]
    files = filesystem[1]
    mocker.patch("os.walk", return_value=fs)
    mocker.patch(patch_utils.format("get_file_sha1"), side_effect=files)

    # Act
    hash = utils.get_folder_sha1("test")

    # Assert
    assert hash == "4bf17af7fa48c5b03a3315a1f2eb17a301ed883a"


@pytest.mark.parametrize("bmark_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("model_uid", rand_l(1, 5000, 2))
@pytest.mark.parametrize("generated_uid", rand_l(1, 5000, 2))
def test__results_path_returns_expected_path(bmark_uid, model_uid, generated_uid):
    # Arrange
    expected_path = f"{config['results_storage']}/{bmark_uid}/{model_uid}/{generated_uid}/{config['results_filename']}"

    # Act
    path = utils.results_path(bmark_uid, model_uid, generated_uid)

    # Assert
    assert path == expected_path
