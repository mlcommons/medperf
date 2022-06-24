from medperf.entities import Result
from medperf.commands.result import ResultsList

PATCH_LIST = "medperf.commands.result.list.{}"


def test_list_gets_local_results(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(Result, "all", return_value=[])

    # Act
    ResultsList.run(comms, ui)

    # Assert
    spy.assert_called_once()


def test_list_gets_remote_results(mocker, comms, ui):
    # Arrange
    mocker.patch.object(Result, "all", return_value=[])
    spy = mocker.patch.object(comms, "get_user_results", return_value=[])

    # Act
    ResultsList.run(comms, ui)

    # Assert
    spy.assert_called_once()
