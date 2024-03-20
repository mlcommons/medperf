from medperf.exceptions import InvalidArgumentError, CleanExit
import pytest
import yaml

from medperf.tests.mocks.dataset import TestDataset
from medperf.commands.dataset.set_operational import DatasetSetOperational

PATCH_OPERATIONAL = "medperf.commands.dataset.set_operational.{}"


@pytest.fixture
def dataset(mocker):
    dset = TestDataset(id=None, state="DEVELOPMENT")
    return dset


@pytest.fixture
def set_operational(mocker, dataset):
    mocker.patch(PATCH_OPERATIONAL.format("Dataset.get"), return_value=dataset)
    dataclass = DatasetSetOperational(None, None)
    return dataclass


def test_validate_fails_if_dataset_already_operational(mocker, set_operational):
    # Arrange
    set_operational.dataset.state = "OPERATION"

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        set_operational.validate()


def test_validate_fails_if_dataset_is_not_marked_as_ready(mocker, set_operational):
    # Arrange
    mocker.patch.object(set_operational.dataset, "is_ready", return_value=False)

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        set_operational.validate()


def test_generate_uids_assigns_uids_to_obj_properties(mocker, set_operational):
    # Arrange
    in_path = ["/usr/data/path", "usr/labels/path"]
    out_path = ["~/.medperf/data/123/data", "~/.medperf/data/123/labels"]
    mocker.patch(PATCH_OPERATIONAL.format("get_folders_hash"), side_effect=lambda x: x)
    mocker.patch.object(set_operational.dataset, "get_raw_paths", return_value=in_path)
    set_operational.dataset.data_path = out_path[0]
    set_operational.dataset.labels_path = out_path[1]

    # Act
    set_operational.generate_uids()

    # Assert
    assert set_operational.dataset.input_data_hash == in_path
    assert set_operational.dataset.generated_uid == out_path


def test_statistics_are_updated(mocker, set_operational, fs):
    # Arrange
    set_operational.dataset.statistics_path = "path"
    contents = {"stats": "stats"}
    fs.create_file("path", contents=yaml.dump(contents))

    # Act
    set_operational.set_statistics()

    # Assert
    assert set_operational.dataset.generated_metadata == contents


def test_update_will_not_update_if_user_rejected(mocker, set_operational, comms):
    # Arrange
    mocker.patch.object(set_operational, "todict")
    mocker.patch(PATCH_OPERATIONAL.format("dict_pretty_print"))
    mocker.patch(PATCH_OPERATIONAL.format("approval_prompt"), return_value=False)
    set_operational.approved = False
    spy = mocker.patch.object(comms, "update_dataset")

    # Act & Assert
    with pytest.raises(CleanExit):
        set_operational.update()

    spy.assert_not_called()
