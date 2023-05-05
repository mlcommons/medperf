import os
from medperf.utils import storage_path
import pytest

import medperf.config as config
from medperf.tests.mocks.cube import TestCube
from medperf.commands.mlcube.submit import SubmitCube

PATCH_MLCUBE = "medperf.commands.mlcube.submit.{}"


@pytest.fixture
def cube(mocker):
    mocker.patch(PATCH_MLCUBE.format("Cube.download"))
    mocker.patch(PATCH_MLCUBE.format("Cube.get_local_hashes"))
    mocker.patch(PATCH_MLCUBE.format("Cube.valid"), return_value=True)
    mocker.patch(PATCH_MLCUBE.format("Cube.upload"))
    mocker.patch(PATCH_MLCUBE.format("Cube.write"))
    return TestCube()


def test_submit_prepares_tmp_path_for_cleanup():
    # Arrange
    cube = TestCube(id=None)

    # Act
    submission = SubmitCube(cube.todict())

    # Assert
    assert submission.cube.path in config.tmp_paths


def test_run_runs_expected_flow(mocker, comms, ui, cube):
    # Arrange
    mock_body = cube.todict()
    # Arrange
    spy_download = mocker.patch(PATCH_MLCUBE.format("SubmitCube.download"))
    spy_cube_upload = mocker.patch(
        PATCH_MLCUBE.format("SubmitCube.upload"), return_value=mock_body
    )
    spy_toper = mocker.patch(PATCH_MLCUBE.format("SubmitCube.to_permanent_path"))
    spy_write = mocker.patch(PATCH_MLCUBE.format("SubmitCube.write"))

    # Act
    SubmitCube.run(cube.todict())

    # Assert
    spy_download.assert_called_once()
    spy_cube_upload.assert_called_once()
    spy_toper.assert_called_once_with(mock_body)
    spy_write.assert_called_once_with(mock_body)


@pytest.mark.parametrize("uid", [858, 2770, 2052])
def test_to_permanent_path_renames_correctly(mocker, comms, ui, cube, uid):
    # Arrange
    cube = TestCube(id=None)
    submission = SubmitCube(cube.todict())
    submission.cube = cube
    spy = mocker.patch("os.rename")
    mocker.patch("os.path.exists", return_value=False)
    old_path = os.path.join(storage_path(config.cubes_storage), cube.generated_uid)
    new_path = os.path.join(storage_path(config.cubes_storage), str(uid))
    # Act
    submission.to_permanent_path({**cube.todict(), "id": uid})

    # Assert
    spy.assert_called_once_with(old_path, new_path)


def test_write_writes_using_entity(mocker, comms, ui, cube):
    submission = SubmitCube(cube.todict())
    spy = mocker.patch(PATCH_MLCUBE.format("Cube.write"))

    # Act
    submission.write(cube.todict())

    # Assert
    spy.assert_called_once_with()


def test_upload_uploads_using_entity(mocker, comms, ui, cube):
    submission = SubmitCube(cube.todict())
    submission.cube = cube
    spy = mocker.patch(PATCH_MLCUBE.format("Cube.upload"))

    # Act
    submission.upload()

    # Assert
    spy.assert_called_once_with()


def test_download_executes_expected_commands(mocker, comms, ui, cube):
    submission = SubmitCube(cube.todict())
    down_spy = mocker.patch(PATCH_MLCUBE.format("Cube.download"))
    valid_spy = mocker.patch(PATCH_MLCUBE.format("Cube.valid"))

    # Act
    submission.download()

    # Assert
    down_spy.assert_called_once_with()
    valid_spy.assert_called_once_with()
