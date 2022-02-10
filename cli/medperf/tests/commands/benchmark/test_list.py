import pytest

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset, Benchmark
from medperf.commands.benchmark.list import BenchmarksList

PATCH_BENCHMARK = "medperf.commands.benchmark.list.{}"


def test_retrieves_all_remote_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_user_benchmarks", return_value=[])

    # Act
    BenchmarksList.run(comms, ui)

    # Assert
    spy.assert_called_once()
