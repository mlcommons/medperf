import pytest

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset, Benchmark
from medperf.commands.dataset.list import DatasetsList

patch_datasets = "medperf.commands.dataset.list.{}"


def test_retrieves_all_benchmarks(mocker, ui):
    # Arrange
    spy = mocker.patch(patch_datasets.format("Dataset.all"), return_value=[])

    # Act
    DatasetsList.run(ui)

    # Assert
    spy.assert_called_once_with(ui)

