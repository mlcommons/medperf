from medperf.entities.result import Result
from medperf.commands.result.list import ResultsList

PATCH_LIST = "medperf.commands.result.list.{}"


def test_list_gets_local_results(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(Result, "all", return_value=[])

    # Act
    ResultsList.run()

    # Assert
    spy.assert_called_once()


def test_list_gets_remote_results(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_results", return_value=[])
    mocker.patch(PATCH_LIST.format("Result._Result__local_all"), return_value=[])

    # Act
    ResultsList.run()

    # Assert
    spy.assert_called_once()


def test_retrieves_all_local_results(mocker, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_LIST.format("Result._Result__local_all"), return_value=[])

    # Act
    ResultsList.run(local=True)

    # Assert
    spy.assert_called_once()


def test_retrieves_user_results(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_user_results", return_value=[])
    mocker.patch(PATCH_LIST.format("Result._Result__local_all"), return_value=[])

    # Act
    ResultsList.run(mine=True)

    # Assert
    spy.assert_called_once()

