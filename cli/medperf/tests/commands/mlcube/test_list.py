import pytest

from medperf.commands.mlcube import CubesList

PATCH_MLCUBE = "medperf.commands.mlcube.list.{}"


def test_list_gets_remote_mlcubes(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "get_user_cubes", return_value=[])

    # Act
    CubesList.run(comms, ui)

    # Assert
    spy.assert_called_once()
