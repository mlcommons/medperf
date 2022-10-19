import os
import pytest
import time_machine
import datetime as dt
from pathlib import Path
from unittest.mock import MagicMock, mock_open, call, ANY

from medperf import utils
import medperf.config as config
from medperf.tests.mocks import MockCube, MockTar

parent = config.storage
data = utils.storage_path(config.data_storage)
cubes = utils.storage_path(config.cubes_storage)
results = utils.storage_path(config.results_storage)
tmp = utils.storage_path(config.tmp_storage)
config_dirs = [parent, data, cubes, results, tmp]
patch_utils = "medperf.utils.{}"


def init_mock_isdir(existing_dirs):
    def isdir(dir):
        return dir in existing_dirs

    return isdir


@pytest.fixture
def datasets(request):
    size = request.param
    uids = list(range(size))
    uids = [str(x) for x in uids]
    uids[-1] = config.tmp_prefix + uids[-1]

    return uids


@pytest.fixture
def dict_with_nones(request):
    num_keys = request.param
    keys = list(range(num_keys))
    vals = list(range(num_keys))
    vals[0] = None
    vals[-1] = None
    return {k: v for k, v in zip(keys, vals)}


@pytest.fixture
def filesystem():
    fs = iter([("/foo", ("bar",), ("baz",)), ("/foo/bar", (), ("spam", "eggs"))])
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
    [config_dirs[0:i] + config_dirs[i + 1:] for i in range(len(config_dirs))],
)
def test_init_storage_creates_nonexisting_paths(mocker, existing_dirs):
    # Arrange
    mock_isdir = init_mock_isdir(existing_dirs)
    mocker.patch("os.path.isdir", side_effect=mock_isdir)
    spy = mocker.patch("os.makedirs")
    exp_mkdirs = list(set(config_dirs) - set(existing_dirs))
    exp_calls = [call(exp_mkdir, exist_ok=True) for exp_mkdir in exp_mkdirs]

    # Act
    utils.init_storage()

    # Assert
    spy.assert_has_calls(exp_calls, any_order=True)


def test_cleanup_removes_temporary_storage(mocker):
    # Arrange
    mocker.patch("os.path.exists", return_value=True)
    spy = mocker.patch(patch_utils.format("rmtree"))
    mocker.patch(patch_utils.format("get_uids"), return_value=[])
    mocker.patch(patch_utils.format("cleanup_benchmarks"))

    # Act
    utils.cleanup()

    # Assert
    spy.assert_called_once_with(tmp)


@pytest.mark.parametrize("datasets", [4, 297, 500, 898], indirect=True)
def test_cleanup_removes_only_invalid_datasets(mocker, datasets):
    # Arrange
    prefix = config.tmp_prefix
    # Mock that the temporary storage path doesn't exist
    mocker.patch("os.path.exists", side_effect=lambda x: x != tmp)
    mocker.patch(patch_utils.format("cleanup_benchmarks"))
    mocker.patch(patch_utils.format("get_uids"), return_value=datasets)
    spy = mocker.patch(patch_utils.format("rmtree"))

    invalid_dsets = [dset for dset in datasets if dset.startswith(prefix)]
    invalid_dsets = [os.path.join(data, dset) for dset in invalid_dsets]
    exp_calls = [call(inv_dset) for inv_dset in invalid_dsets]

    # Act
    utils.cleanup()

    # Assert
    spy.assert_has_calls(exp_calls, any_order=True)
    # Account for the tmp_storage call
    assert spy.call_count == len(exp_calls)


@pytest.mark.parametrize("path", ["path/to/uids", "~/.medperf/cubes/"])
@pytest.mark.parametrize("datasets", [4, 287], indirect=True)
def test_get_uids_returns_uids_of_datasets(mocker, datasets, path):
    # Arrange
    mock_walk_return = iter([(data, datasets, ())])
    spy = mocker.patch("os.walk", return_value=mock_walk_return)

    # Act
    dsets = utils.get_uids(path)

    # Assert
    assert dsets == datasets
    spy.assert_called_once_with(path)


@pytest.mark.parametrize("msg", ["test", "error message", "can't find cube"])
def test_pretty_error_displays_message(mocker, ui, msg):
    # Arrange
    spy = mocker.patch.object(ui, "print_error")
    mocker.patch(patch_utils.format("cleanup"))
    mocker.patch(patch_utils.format("sys.exit"))

    # Act
    utils.pretty_error(msg)

    # Assert
    printed_msg = spy.call_args_list[0][0][0]
    assert msg in printed_msg


@pytest.mark.parametrize("clean", [True, False])
def test_pretty_error_runs_cleanup_when_requested(mocker, ui, clean):
    # Arrange
    spy = mocker.patch(patch_utils.format("cleanup"))
    mocker.patch("typer.echo")
    mocker.patch(patch_utils.format("sys.exit"))

    # Act
    utils.pretty_error("test", clean)

    # Assert
    if clean:
        spy.assert_called_once()
    else:
        spy.assert_not_called()


def test_pretty_error_exits_program(mocker, ui):
    # Arrange
    mocker.patch(patch_utils.format("cleanup"))
    mocker.patch("typer.echo")
    spy = mocker.patch(patch_utils.format("sys.exit"))

    # Act
    utils.pretty_error("test")

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("timeparams", [(2000, 10, 23), (2021, 1, 2), (2012, 5, 24)])
@pytest.mark.parametrize("salt", [342, 87])
def test_generate_tmp_datapath_creates_expected_path(mocker, timeparams, salt):
    # Arrange
    datetime = dt.datetime(*timeparams)
    traveller = time_machine.travel(datetime)
    traveller.start()
    timestamp = dt.datetime.timestamp(datetime)
    mocker.patch("os.path.isdir", return_value=False)
    mocker.patch("random.randint", return_value=salt)
    tmp_path = f"{config.tmp_prefix}{int(timestamp + salt)}"
    exp_out_path = os.path.join(data, tmp_path)

    # Act
    out_path = utils.generate_tmp_datapath()

    # Assert
    assert out_path == exp_out_path
    traveller.stop()


@pytest.mark.parametrize("is_valid", [True, False])
def test_cube_validity_fails_when_invalid(mocker, ui, is_valid):
    # Arrange
    spy = mocker.patch(patch_utils.format("pretty_error"))
    cube = MockCube(is_valid)

    # Act
    utils.check_cube_validity(cube)

    # Assert
    if not is_valid:
        spy.assert_called_once()
    else:
        spy.assert_not_called()


@pytest.mark.parametrize("file", ["test.tar.bz", "path/to/file.tar.bz"])
def test_untar_opens_specified_file(mocker, file):
    # Arrange
    spy = mocker.patch("tarfile.open")
    mocker.patch("tarfile.TarFile.extractall")
    mocker.patch("tarfile.TarFile.close")
    mocker.patch("os.remove")

    # Act
    utils.untar(file)

    # Assert
    spy.assert_called_once_with(file)


@pytest.mark.parametrize("file", ["./test.tar.bz", "path/to/file.tar.bz"])
def test_untar_extracts_to_parent_directory(mocker, file):
    # Arrange
    parent_path = str(Path(file).parent)
    mocker.patch("tarfile.open", return_value=MockTar())
    spy = mocker.spy(MockTar, "extractall")
    mocker.patch("os.remove")

    # Act
    utils.untar(file)

    # Assert
    spy.assert_called_once_with(ANY, parent_path)


@pytest.mark.parametrize("file", ["./test.tar.bz", "path/to/file.tar.bz"])
def test_untar_removes_tarfile(mocker, file):
    # Arrange
    mocker.patch("tarfile.open")
    mocker.patch("tarfile.TarFile.extractall")
    mocker.patch("tarfile.TarFile.close")
    spy = mocker.patch("os.remove")

    # Act
    utils.untar(file)

    # Assert
    spy.assert_called_once_with(file)


def test_approval_prompt_asks_for_user_input(mocker, ui):
    # Arrange
    spy = mocker.patch.object(ui, "prompt", return_value="y")

    # Act
    utils.approval_prompt("test")

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
    utils.approval_prompt("test prompt")

    # Assert
    spy.call_count == exp_repeats


@pytest.mark.parametrize("input_val", ["Y", "y", "N", "n"])
def test_approval_prompt_returns_approved_boolean(mocker, ui, input_val):
    # Arrange
    mocker.patch.object(ui, "prompt", return_value=input_val)

    # Act
    approved = utils.approval_prompt("test approval return")

    # Assert
    assert approved == (input_val in "yY")


@pytest.mark.parametrize("dict_with_nones", [32, 7, 90], indirect=True)
def test_dict_pretty_print_passes_clean_dict_to_yaml(mocker, ui, dict_with_nones):
    # Arrange
    mocker.patch("typer.echo")
    spy = mocker.patch("yaml.dump", return_value="")
    exp_dict = {k: v for k, v in dict_with_nones.items() if v is not None}

    # Act
    utils.dict_pretty_print(dict_with_nones)

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


@pytest.mark.parametrize("bmk", [1, 2])
@pytest.mark.parametrize("model", [23, 84])
@pytest.mark.parametrize("gen_uid", [43, 8])
def test__results_path_returns_expected_path(bmk, model, gen_uid):
    # Arrange
    storage = config.storage
    res_storage = config.results_storage
    expected_path = f"{storage}/{res_storage}/{bmk}/{model}/{gen_uid}"

    # Act
    path = utils.results_path(bmk, model, gen_uid)

    # Assert
    assert path == expected_path


@pytest.mark.parametrize(
    "encode_pair",
    [(float("nan"), "nan"), (float("inf"), "Infinity"), (float("-inf"), "-Infinity")],
)
def test_sanitize_json_encodes_invalid_nums(mocker, encode_pair):
    # Arrange
    val, exp_encoding = encode_pair
    body = {"test": val}

    # Act
    sanitized_dict = utils.sanitize_json(body)

    # Assert
    assert sanitized_dict["test"] == exp_encoding


@pytest.mark.parametrize("path", ["stats_path", "path/to/folder"])
def test_get_stats_opens_stats_path(mocker, path):
    # Arrange
    spy = mocker.patch("builtins.open", MagicMock())
    mocker.patch(patch_utils.format("yaml.safe_load"), return_value={})
    mocker.patch(patch_utils.format("os.remove"))
    opened_path = os.path.join(path, config.statistics_filename)
    # Act
    utils.get_stats(path)

    # Assert
    spy.assert_called_once_with(opened_path, "r")


@pytest.mark.parametrize("stats", [{}, {"test": ""}, {"mean": 8}])
def test_get_stats_returns_stats(mocker, stats):
    # Arrange
    mocker.patch("builtins.open", MagicMock())
    mocker.patch(patch_utils.format("os.remove"))
    mocker.patch(patch_utils.format("yaml.safe_load"), return_value=stats)

    # Act
    returned_stats = utils.get_stats("mocked_path")

    # Assert
    assert returned_stats == stats


def test_get_stats_removes_file_by_default(mocker):
    # Arrange
    path = "mocked_path"
    mocker.patch("builtins.open", MagicMock())
    spy = mocker.patch(patch_utils.format("os.remove"))
    mocker.patch(patch_utils.format("yaml.safe_load"))
    opened_path = os.path.join(path, config.statistics_filename)

    # Act
    utils.get_stats(path)

    # Assert
    spy.assert_called_once_with(opened_path)


@pytest.mark.parametrize("results", [{}, {"test": ""}, {"mean": 8}])
def test_get_results_returns_results(mocker, results):
    # Arrange
    mocker.patch("builtins.open", MagicMock())
    mocker.patch(patch_utils.format("os.remove"))
    mocker.patch(patch_utils.format("yaml.safe_load"), return_value=results)

    # Act
    returned_results = utils.get_results("mocked_path")

    # Assert
    assert returned_results == results


def test_get_results_removes_file_by_default(mocker):
    # Arrange
    path = "mocked_path"
    mocker.patch("builtins.open", MagicMock())
    spy = mocker.patch(patch_utils.format("os.remove"))
    mocker.patch(patch_utils.format("yaml.safe_load"))
    opened_path = os.path.join(path, config.results_filename)

    # Act
    utils.get_results(path)

    # Assert
    spy.assert_called_once_with(opened_path)
