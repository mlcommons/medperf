import os
import pytest
import logging
from pathlib import Path
from unittest.mock import mock_open, call, ANY

from medperf import utils
import medperf.config as config
from medperf.tests.mocks import MockTar
from medperf.exceptions import MedperfException
import yaml

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


@pytest.mark.parametrize(
    "text,exp_output",
    [
        ("password: '123'", "password: [redacted]"),
        ("password='test'", "password=[redacted]"),
        ('token="2872547"', "token=[redacted]"),
        ("{'token': '279438'}", "{'token': [redacted]}"),
    ],
)
def test_setup_logging_filters_sensitive_data(text, exp_output):
    # Arrange
    logging.getLogger().setLevel("DEBUG")
    log_file = os.path.join(config.logs_storage, config.log_file)

    # Act
    logging.debug(text)

    # Assert
    with open(log_file) as f:
        data = f.read()

    assert exp_output in data


@pytest.mark.parametrize("file", ["./test.txt", "../file.yaml", "folder/file.zip"])
def test_get_file_hash_opens_specified_file(mocker, file):
    # Arrange
    spy = mocker.patch("builtins.open", mock_open())

    # Act
    utils.get_file_hash(file)

    # Assert
    spy.assert_called_once_with(file, "rb")


@pytest.mark.parametrize(
    "file_io",
    [
        (
            b"test file\n",
            "55f8718109829bf506b09d8af615b9f107a266e19f7a311039d1035f180b22d4",
        ),
        (
            b"file\nwith\nmultilines\n",
            "7361d0aa589a45156d130cfde89f8ad441770fd87d992f404e5758ece6d36b49",
        ),
    ],
)
def test_get_file_hash_calculates_hash(mocker, file_io):
    # Arrange
    file_contents, expected_hash = file_io
    mocker.patch("builtins.open", mock_open(read_data=file_contents))

    # Act
    hash = utils.get_file_hash("")

    # Assert
    assert hash == expected_hash


def test_cleanup_removes_files(mocker, ui, fs):
    # Arrange
    path = "/path/to/garbage.html"
    fs.create_file(path, contents="garbage")
    config.tmp_paths = [path]

    # Act
    utils.cleanup()

    # Assert
    assert not os.path.exists(path)


def test_cleanup_moves_files_to_trash_on_failure(mocker, ui, fs):
    # Arrange
    path = "/path/to/garbage.html"
    fs.create_file(path, contents="garbage")
    config.tmp_paths = [path]

    def side_effect(*args, **kwargs):
        raise PermissionError

    mocker.patch("os.remove", side_effect=side_effect)
    trash_folder = config.trash_folder

    # Act
    utils.cleanup()

    # Assert
    trash_id = os.listdir(trash_folder)[0]
    exp_path = os.path.join(trash_folder, trash_id, os.path.basename(path))
    assert os.path.exists(exp_path)


@pytest.mark.parametrize("path", ["path/to/uids", "~/.medperf/cubes/"])
@pytest.mark.parametrize("datasets", [4, 287], indirect=True)
def test_get_uids_returns_uids_of_datasets(mocker, datasets, path):
    # Arrange
    mock_walk_return = iter([(config.datasets_folder, datasets, ())])
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

    # Act
    utils.pretty_error(msg)

    # Assert
    printed_msg = spy.call_args_list[0][0][0]
    assert msg in printed_msg


@pytest.mark.parametrize("file", ["test.tar.bz", "path/to/file.tar.bz"])
def test_untar_opens_specified_file(mocker, file):
    # Arrange
    spy = mocker.patch("tarfile.open")
    mocker.patch("tarfile.TarFile.extractall")
    mocker.patch("tarfile.TarFile.close")
    mocker.patch(patch_utils.format("remove_path"))

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
    mocker.patch(patch_utils.format("remove_path"))

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
    spy = mocker.patch(patch_utils.format("remove_path"))

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


def test_get_folders_hash_hashes_all_files_in_folder(mocker, filesystem):
    # Arrange
    fs = filesystem[0]
    files = filesystem[1]
    exp_calls = [call(file) for file in files]
    mocker.patch("os.walk", return_value=fs)
    spy = mocker.patch(patch_utils.format("get_file_hash"), side_effect=files)

    # Act
    utils.get_folders_hash(["test"])

    # Assert
    spy.assert_has_calls(exp_calls)


def test_get_folders_hash_sorts_individual_hashes(mocker, filesystem):
    # Arrange
    fs = filesystem[0]
    files = filesystem[1]
    mocker.patch("os.walk", return_value=fs)
    mocker.patch(patch_utils.format("get_file_hash"), side_effect=files)
    spy = mocker.patch("builtins.sorted", side_effect=sorted)

    # Act
    utils.get_folders_hash(["test"])

    # Assert
    spy.assert_called_once_with(files)


def test_get_folders_hash_returns_expected_hash(mocker, filesystem):
    # Arrange
    fs = filesystem[0]
    files = filesystem[1]
    mocker.patch("os.walk", return_value=fs)
    mocker.patch(patch_utils.format("get_file_hash"), side_effect=files)

    # Act
    hash = utils.get_folders_hash(["test"])

    # Assert
    assert hash == "b7e9365f1e796ba29e9e6b1b94b5f4cc7238530601fad8ec96ece9fee68c3d7f"


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


@pytest.mark.parametrize(
    "error_dict,expected_out",
    [
        (
            {"name": ["can't be a duplicate", "must be longer"]},
            "\n- name: \n\t- can't be a duplicate\n\t- must be longer",
        ),
        (
            {"detail": "You do not have permission to perform this action"},
            "\n- detail: You do not have permission to perform this action",
        ),
        (
            {("field1",): "error1", "field2": ["error2", "error3"]},
            "\n- field1: error1\n- field2: \n\t- error2\n\t- error3",
        ),
    ],
)
def test_format_errors_dict_correctly_formats_all_expected_inputs(
    error_dict, expected_out
):
    # Act
    out = utils.format_errors_dict(error_dict)

    # Assert
    assert out == expected_out


def test_get_cube_image_name_retrieves_name(mocker, fs):
    # Arrange
    exp_image_name = "some_image_name"
    cube_path = "path"

    mock_content = {"singularity": {"image": exp_image_name}}
    target_file = os.path.join(cube_path, config.cube_filename)
    fs.create_file(target_file, contents=yaml.dump(mock_content))

    # Act
    image_name = utils.get_cube_image_name(cube_path)

    # Assert
    assert exp_image_name == image_name


def test_get_cube_image_name_fails_if_cube_not_configured(mocker, fs):
    # Arrange
    exp_image_name = "some_image_name"
    cube_path = "path"

    mock_content = {"not singularity": {"image": exp_image_name}}
    target_file = os.path.join(cube_path, config.cube_filename)
    fs.create_file(target_file, contents=yaml.dump(mock_content))

    # Act & Assert
    with pytest.raises(MedperfException):
        utils.get_cube_image_name(cube_path)
