import pytest

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset, Benchmark
from medperf.commands.dataset.list import DatasetsList

PATCH_DATASETS = "medperf.commands.dataset.list.{}"


def test_retrieves_all_local_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_DATASETS.format("Dataset.all"), return_value=[])

    # Act
    DatasetsList.run(comms, ui)

    # Assert
    spy.assert_called_once_with(ui)


def test_retrieves_all_remote_benchmarks(mocker, comms, ui):
    # Arrange
    mocker.patch(PATCH_DATASETS.format("Dataset.all"), return_value=[])
    spy = mocker.patch.object(comms, "get_user_datasets", return_value=[])

    # Act
    DatasetsList.run(comms, ui)

    # Assert
    spy.assert_called_once()
