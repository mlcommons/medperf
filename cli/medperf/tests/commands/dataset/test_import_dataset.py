import os
from medperf import config
from medperf.exceptions import ExecutionError, InvalidArgumentError
import pytest

from medperf.tests.mocks.dataset import TestDataset
from medperf.commands.dataset.import_dataset import ImportDataset


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


def test_import_extracts_files_show_folder(mocker, import_dataset, fs):

    # Arrange
    untar_files_spy = mocker.patch(PATCH_IMPORT.format("untar"), return_value="")
    import_dataset.input_path = "/testfile"
    fs.create_file(import_dataset.input_path)
    copy_tar_file_spy = mocker.patch(PATCH_IMPORT.format("copy_file"))

    # Act
    import_dataset.untar_files()

    # Assert
    assert config.dataset_backup_foldername in import_dataset.tarfiles
    copy_tar_file_spy.assert_called_once()
    untar_files_spy.assert_called_once()


def test_import_fails_if_yaml_file_does_not_exist(import_dataset):

    # Arrange
    import_dataset.tarfiles = config.dataset_backup_foldername
    os.makedirs(import_dataset.tarfiles)

    # Act & Assert
    with pytest.raises(
        ExecutionError, match="Dataset backup is invalid, config file doesn't exist"
    ):
        import_dataset.validate()


def test_import_fails_if_dataset_folder_not_found(mocker, import_dataset, fs):

    # Arrange
    import_dataset.tarfiles = config.dataset_backup_foldername
    os.makedirs(os.path.join(import_dataset.tarfiles, "test"))
    fs.create_file(os.path.join(import_dataset.tarfiles, config.backup_config_filename))
    mocker.patch("yaml.safe_load", return_value={"dataset": "not_test"})

    # Act & Assert
    with pytest.raises(
        ExecutionError, match="Dataset backup is invalid, dataset folders not found"
    ):
        import_dataset.validate()


def test_import_fails_if_development_dataset_raw_folders_does_not_exist(
    mocker, import_dataset, fs
):

    # Arrange
    import_dataset.tarfiles = config.dataset_backup_foldername
    os.makedirs(os.path.join(import_dataset.tarfiles, "test"))
    os.makedirs(os.path.join(import_dataset.tarfiles, "data"))
    os.makedirs(os.path.join(import_dataset.tarfiles, "labels"))
    fs.create_file(os.path.join(import_dataset.tarfiles, config.backup_config_filename))
    mocker.patch(
        "yaml.safe_load", return_value={"dataset": "test", "data": "", "labels": ""}
    )

    # Act & Assert
    with pytest.raises(
        ExecutionError, match="Dataset backup is invalid, config file is invalid"
    ):
        import_dataset.validate()


def test_import_fails_if_dataset_already_exist(mocker, import_dataset, fs):

    # Arrange
    import_dataset.dataset_path = "/test"
    import_dataset.dataset.data_path = "/test/data"
    os.makedirs(import_dataset.dataset.data_path)
    fs.create_file(
        os.path.join(import_dataset.dataset.data_path, "testfile")
    )  # Create a fake file to stimulate that dataset folders contains data

    # Act & Assert
    with pytest.raises(ExecutionError, match=r"Dataset '.*' already exists."):
        import_dataset._validate_dataset()


def test_import_fails_if_imported_dataset_id_does_not_match_the_id_in_backup(
    mocker, import_dataset, fs
):

    # Arrange
    import_dataset.tarfiles = config.dataset_backup_foldername
    os.makedirs(os.path.join(import_dataset.tarfiles, "test"))
    os.makedirs(os.path.join(import_dataset.tarfiles, "data"))
    os.makedirs(os.path.join(import_dataset.tarfiles, "labels"))
    fs.create_file(os.path.join(import_dataset.tarfiles, config.backup_config_filename))
    mocker.patch(
        "yaml.safe_load",
        return_value={"dataset": "test", "data": "data", "labels": "labels"},
    )
    import_dataset.dataset_id = "test1"
    import_dataset.dataset_path = "/test"
    import_dataset.dataset.data_path = "/test/data"
    import_dataset.dataset.labels_path = "/test/labels"
    os.makedirs(import_dataset.dataset.data_path)
    os.makedirs(import_dataset.dataset.labels_path)
    # Act & Assert
    with pytest.raises(
        InvalidArgumentError, match="Cannot import dataset '.*' data to dataset '.*'"
    ):
        import_dataset.validate()


def test_import_fails_if_imported_dataset_server_does_not_match_profile_server(
    mocker, import_dataset, fs
):

    # Arrange
    import_dataset.tarfiles = config.dataset_backup_foldername
    os.makedirs(os.path.join(import_dataset.tarfiles, "test"))
    os.makedirs(os.path.join(import_dataset.tarfiles, "data"))
    os.makedirs(os.path.join(import_dataset.tarfiles, "labels"))
    fs.create_file(os.path.join(import_dataset.tarfiles, config.backup_config_filename))
    mocker.patch(
        "yaml.safe_load",
        return_value={
            "dataset": "test",
            "data": "data",
            "labels": "labels",
            "server": "localhost_8000",
        },
    )
    import_dataset.dataset_id = "test"
    import_dataset.dataset_path = "/test"
    import_dataset.dataset.data_path = "/test/data"
    import_dataset.dataset.labels_path = "/test/labels"
    os.makedirs(import_dataset.dataset.data_path)
    os.makedirs(import_dataset.dataset.labels_path)
    config.server = "api_medperf_org"

    # Act & Assert
    with pytest.raises(
        ExecutionError, match="Cannot import .+ dataset backup to .+ server!"
    ):
        import_dataset.validate()
