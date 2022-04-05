from medperf.commands.benchmark.list import BenchmarksList

PATCH_BENCHMARK = "medperf.commands.benchmark.list.{}"


def test_retrieves_user_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_user_benchmarks", return_value=[])

    # Act
    BenchmarksList.run(comms, ui)

    # Assert
    spy.assert_called_once()


def test_all_retrieves_all_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_benchmarks", return_value=[])

    # Act
    BenchmarksList.run(comms, ui, all=True)

    # Assert
    spy.assert_called_once()
