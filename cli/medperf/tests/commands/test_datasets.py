import pytest

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset, Benchmark
from medperf.commands.dataset.list import Datasets

patch_datasets = "medperf.commands.datasets.{}"


def test_retrieves_all_benchmarks(mocker, ui):
    # Arrange
    spy = mocker.patch(patch_datasets.format("Dataset.all"), return_value=[])

    # Act
    Datasets.run(ui)

    # Assert
    spy.assert_called_once_with(ui)

