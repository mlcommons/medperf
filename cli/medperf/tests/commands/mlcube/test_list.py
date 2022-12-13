from medperf.commands.mlcube.list import CubesList

PATCH_MLCUBE = "medperf.commands.mlcube.list.{}"


def test_list_gets_remote_mlcubes(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_cubes", return_value=[])
    mocker.patch(PATCH_MLCUBE.format("Cube._Cube__local_all"), return_value=[])

    # Act
    CubesList.run()

    # Assert
    spy.assert_called_once()


def test_all_retrieves_all_local_mlcubes(mocker, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_MLCUBE.format("Cube._Cube__local_all"), return_value=[])

    # Act
    CubesList.run(local=True)

    # Assert
    spy.assert_called_once()


def test_all_retrieves_all_user_mlcubes(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_user_cubes", return_value=[])
    mocker.patch(PATCH_MLCUBE.format("Cube._Cube__local_all"), return_value=[])

    # Act
    CubesList.run(mine=True)

    # Assert
    spy.assert_called_once()
