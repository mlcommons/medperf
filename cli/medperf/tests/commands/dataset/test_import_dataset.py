import os
from medperf import config
from medperf.exceptions import ExecutionError, InvalidArgumentError
import pytest

from medperf.tests.mocks.dataset import TestDataset
from medperf.commands.dataset.import_dataset import ImportDataset
import yaml

PATCH_IMPORT = "medperf.commands.dataset.import_dataset.{}"


@pytest.fixture
def dataset():
    dset = TestDataset(id=None, state="DEVELOPMENT")
    return dset


@pytest.fixture
def import_dataset(mocker, dataset):
    mocker.patch(PATCH_IMPORT.format("Dataset.get"), return_value=dataset)
    dataclass = ImportDataset("", "", None)
    return dataclass


def test_import_fails_if_input_path_not_provided_for_development_datasets(
    import_dataset,
):

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        import_dataset.validate_input()


def test_import_fails_if_input_path_does_not_exist(import_dataset):

    # Arrange
    import_dataset.input_path = "/test.gz"

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        import_dataset.validate_input()


def test_import_fails_if_input_path_is_not_a_file(import_dataset):

    # Arrange
    import_dataset.input_path = "/testfolder"
    os.makedirs(import_dataset.input_path)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        import_dataset.validate_input()


def test_import_fails_if_raw_data_path_does_not_exist(import_dataset):

    # Arrange
    import_dataset.raw_data_path = "/test"

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        import_dataset.validate_input()


def test_import_fails_if_raw_data_path_is_a_file(import_dataset, fs):

    # Arrange
    import_dataset.raw_data_path = "/testfile"
    fs.create_file(import_dataset.raw_data_path)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        import_dataset.validate_input()


def test_import_dataset_with_non_tar_file(import_dataset, fs):

    # Arrange
    import_dataset.input_path = "/testfile"
    fs.create_file(import_dataset.input_path)

    # Act & Assert
    with pytest.raises(ExecutionError):
        import_dataset.untar_files()


def test_import_fails_if_archive_config_does_not_exist(import_dataset):

    # Arrange
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs(import_dataset.tarfiles)

    # Act & Assert
    with pytest.raises(
        ExecutionError, match="Dataset archive is invalid, config file doesn't exist"
    ):
        import_dataset.validate()


def test_import_fails_if_archive_config_has_no_dataset_key(mocker, fs, import_dataset):

    # Arrange
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs(import_dataset.tarfiles)
    config_file = os.path.join(import_dataset.tarfiles, config.archive_config_filename)
    contents = yaml.dump({})
    fs.create_file(config_file, contents=contents)

    # Act & Assert
    with pytest.raises(
        InvalidArgumentError, match="Invalid archive config: dataset key not found"
    ):
        import_dataset.validate()


def test_import_fails_if_archive_config_has_no_server_key(mocker, fs, import_dataset):

    # Arrange
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs(import_dataset.tarfiles)
    config_file = os.path.join(import_dataset.tarfiles, config.archive_config_filename)
    contents = yaml.dump({"dataset": 1})
    fs.create_file(config_file, contents=contents)

    # Act & Assert
    with pytest.raises(
        InvalidArgumentError, match="Invalid archive config: server key not found"
    ):
        import_dataset.validate()


def test_import_fails_if_archive_config_has_no_raw_data_keys(
    mocker, fs, import_dataset
):

    # Arrange
    import_dataset.dataset.state = "DEVELOPMENT"
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs(import_dataset.tarfiles)
    config_file = os.path.join(import_dataset.tarfiles, config.archive_config_filename)
    contents = yaml.dump({"dataset": 1, "server": "some_server"})
    fs.create_file(config_file, contents=contents)

    # Act & Assert
    with pytest.raises(
        InvalidArgumentError, match="Invalid archive config: raw data keys not found"
    ):
        import_dataset.validate()


def test_import_fails_if_archive_config_has_incorrect_data_id(
    mocker, fs, import_dataset
):

    # Arrange
    import_dataset.dataset.state = "DEVELOPMENT"
    import_dataset.dataset_id = 2
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs(import_dataset.tarfiles)
    config_file = os.path.join(import_dataset.tarfiles, config.archive_config_filename)
    contents = yaml.dump(
        {
            "dataset": 1,
            "server": "some_server",
            "raw_data": "rawdata",
            "raw_labels": "rawlabels",
        }
    )
    fs.create_file(config_file, contents=contents)

    # Act & Assert
    with pytest.raises(
        InvalidArgumentError,
        match="The archive dataset is '1' while specified dataset is '2'",
    ):
        import_dataset.validate()


def test_import_fails_if_archive_config_has_incorrect_server(
    mocker, fs, import_dataset
):

    # Arrange
    import_dataset.dataset.state = "OPERATION"
    import_dataset.dataset_id = 1
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs(import_dataset.tarfiles)
    config_file = os.path.join(import_dataset.tarfiles, config.archive_config_filename)
    contents = yaml.dump({"dataset": 1, "server": "some_server_not_like_config.server"})
    fs.create_file(config_file, contents=contents)

    # Act & Assert
    with pytest.raises(
        InvalidArgumentError, match="Dataset export was done for a different server"
    ):
        import_dataset.validate()


def test_import_fails_if_prepared_data_not_found_in_archive(mocker, fs, import_dataset):

    # Arrange
    import_dataset.dataset.state = "OPERATION"
    import_dataset.dataset_id = 1
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs(import_dataset.tarfiles)
    config_file = os.path.join(import_dataset.tarfiles, config.archive_config_filename)
    contents = yaml.dump({"dataset": 1, "server": config.server})
    fs.create_file(config_file, contents=contents)

    # Act & Assert
    with pytest.raises(ExecutionError, match="No prepared dataset in archive"):
        import_dataset.validate()


def test_import_fails_if_data_already_exists(mocker, fs, import_dataset):

    # Arrange
    import_dataset.dataset.state = "OPERATION"
    import_dataset.dataset_id = 1
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs("/some_empty_folder/1")
    config_file = os.path.join(import_dataset.tarfiles, config.archive_config_filename)
    contents = yaml.dump({"dataset": 1, "server": config.server})
    fs.create_file(config_file, contents=contents)
    os.makedirs(import_dataset.dataset.data_path)
    os.makedirs(import_dataset.dataset.labels_path)

    # Act & Assert
    with pytest.raises(ExecutionError, match="Dataset '1' already exists locally."):
        import_dataset.validate()


def test_import_fails_if_raw_data_not_found_in_archive(mocker, fs, import_dataset):

    # Arrange
    import_dataset.dataset.state = "DEVELOPMENT"
    import_dataset.dataset_id = 1
    import_dataset.tarfiles = "/some_empty_folder"
    os.makedirs("/some_empty_folder/1")
    config_file = os.path.join(import_dataset.tarfiles, config.archive_config_filename)
    contents = yaml.dump(
        {
            "dataset": 1,
            "server": config.server,
            "raw_data": "rawdata",
            "raw_labels": "rawlabels",
        }
    )
    fs.create_file(config_file, contents=contents)

    # Act & Assert
    with pytest.raises(ExecutionError, match="No raw data in archive"):
        import_dataset.validate()
