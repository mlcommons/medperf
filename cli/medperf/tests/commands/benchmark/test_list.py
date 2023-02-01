from medperf.commands.benchmark.list import BenchmarksList

PATCH_BENCHMARK = "medperf.commands.benchmark.list.{}"


def test_retrieves_all_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_benchmarks", return_value=[])
    mocker.patch(
        PATCH_BENCHMARK.format("Benchmark._Benchmark__local_all"), return_value=[]
    )

    # Act
    BenchmarksList.run()

    # Assert
    spy.assert_called_once()


def test_local_retrieves_local_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_benchmarks", return_value=[])
    local_spy = mocker.patch(
        PATCH_BENCHMARK.format("Benchmark._Benchmark__local_all"), return_value=[]
    )

    # Act
    BenchmarksList.run(local=True)

    # Assert
    spy.assert_not_called()
    local_spy.assert_called_once()


def test_user_retrieves_user_benchmarks(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_user_benchmarks", return_value=[])
    mocker.patch(
        PATCH_BENCHMARK.format("Benchmark._Benchmark__local_all"), return_value=[]
    )

    # Act
    BenchmarksList.run(mine=True)

    # Assert
    spy.assert_called_once()
