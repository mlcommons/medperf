import os
from medperf.exceptions import ExecutionError
import pytest

from medperf.tests.mocks.dataset import TestDataset
from medperf.commands.dataset.export_dataset import ExportDataset


PATCH_EXPORT = "medperf.commands.dataset.export_dataset.{}"


@pytest.fixture
def dataset(mocker):
    dset = TestDataset(id=None, state="DEVELOPMENT")
    return dset


@pytest.fixture
def export_dataset(mocker, dataset):
    mocker.patch(PATCH_EXPORT.format("Dataset.get"), return_value=dataset)
    dataclass = ExportDataset("", "")
    return dataclass


def test_export_fail_if_development_dataset_raw_paths_does_not_exist(
    mocker, export_dataset
):

    # Arrange
    mocker.patch(
        PATCH_EXPORT.format("Dataset.get_raw_paths"), return_value=["test", "test1"]
    )

    # Act & Assert
    with pytest.raises(ExecutionError):
        export_dataset.prepare()


def test_export_if_development_dataset_length_of_yaml_paths_keys_equal_4(
    mocker, export_dataset, fs
):

    # Arrange
    mocker.patch(
        PATCH_EXPORT.format("Dataset.get_raw_paths"), return_value=["/test", "/test1"]
    )
    os.makedirs("/test")
    os.makedirs("/test1")
    fs.create_file("/test/testfile")
    fs.create_file("/test1/testfile")

    # Act
    export_dataset.prepare()

    # Assert
    assert len(export_dataset.archive_config.keys()) == 4


def test_export_if_operation_dataset_length_of_yaml_paths_keys_equal_2(export_dataset):

    # Arrange
    export_dataset.dataset.state = "OPERATION"

    # Act
    export_dataset.prepare()

    # Assert
    assert len(export_dataset.archive_config.keys()) == 2


def test_export_if_operation_dataset_number_of_folders_to_archive(export_dataset):

    # Arrange
    export_dataset.dataset.state = "OPERATION"

    # Act
    export_dataset.prepare()

    # Assert
    assert len(export_dataset.folders_paths) == 2


def test_export_if_development_dataset_number_of_folders_to_archive(
    mocker, fs, export_dataset
):

    # Arrange
    mocker.patch(
        PATCH_EXPORT.format("Dataset.get_raw_paths"), return_value=["/test", "/test1"]
    )
    os.makedirs("/test")
    os.makedirs("/test1")
    fs.create_file("/test/testfile")
    fs.create_file("/test1/testfile")

    export_dataset.dataset.state = "DEVELOPMENT"

    # Act
    export_dataset.prepare()

    # Assert
    assert len(export_dataset.folders_paths) == 4


def test_export_if_development_dataset_with_same_raw_paths_number_of_folders_to_archive(
    mocker, fs, export_dataset
):

    # Arrange
    mocker.patch(
        PATCH_EXPORT.format("Dataset.get_raw_paths"), return_value=["/test", "/test"]
    )
    os.makedirs("/test")
    fs.create_file("/test/testfile")
    export_dataset.dataset.state = "DEVELOPMENT"

    # Act
    export_dataset.prepare()

    # Assert
    assert len(export_dataset.folders_paths) == 3


def test_export_if_tar_gz_file_is_created_at_output_path(export_dataset):

    # Arrange
    export_dataset.dataset.state = "OPERATION"
    export_dataset.dataset_id = "1"
    export_dataset.output_path = f"/test/{export_dataset.dataset_id}.gz"
    os.makedirs("/test/")

    # Act
    export_dataset.create_tar()

    # Assert
    assert os.path.exists(export_dataset.output_path) is True
