from __future__ import annotations
import os
import pytest

import medperf.config as config
from medperf.tests.mocks.cube import TestCube
from medperf.commands.mlcube.submit import SubmitCube
from medperf.exceptions import InvalidArgumentError

PATCH_MLCUBE = "medperf.commands.mlcube.submit.{}"


# rename ficture to submission and change all its usage below
@pytest.fixture
def submission(mocker):
    mocker.patch(PATCH_MLCUBE.format("Cube.download_run_files"))
    mocker.patch(PATCH_MLCUBE.format("Cube.upload"))
    mocker.patch(PATCH_MLCUBE.format("Cube.write"))
    cube = TestCube().todict()
    container_config = cube.pop("container_config")
    parameters_config = cube.pop("parameters_config")

    submission = SubmitCube(cube, "some/path")
    submission.container_config = container_config
    submission.parameters_config = parameters_config
    submission.create_cube_object()

    return submission


def test_validate_raises_when_encrypted_without_key(mocker, submission):
    # Arrange
    mocker.patch.object(submission.cube, "is_encrypted", return_value=True)
    submission.decryption_key = None

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        submission.validate()


def test_validate_raises_when_not_encrypted_with_key(mocker, submission):
    # Arrange
    mocker.patch.object(submission.cube, "is_encrypted", return_value=False)
    submission.decryption_key = "some_key"

    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        submission.validate()


def test_download_executes_expected_commands2(mocker, comms, ui, submission):
    run_down_spy = mocker.patch(PATCH_MLCUBE.format("Cube.download_run_files"))

    # Act
    submission.download_run_files()

    # Assert
    run_down_spy.assert_called_once_with()


@pytest.mark.parametrize("uid", [858, 2770, 2052])
def test_to_permanent_path_renames_correctly(mocker, comms, ui, submission, uid):
    # Arrange
    cube = TestCube(id=None)
    submission.cube = cube
    spy = mocker.patch("os.rename")
    mocker.patch("os.path.exists", return_value=False)
    old_path = os.path.join(config.cubes_folder, cube.local_id)
    new_path = os.path.join(config.cubes_folder, str(uid))
    # Act
    submission.to_permanent_path({**cube.todict(), "id": uid})

    # Assert
    spy.assert_called_once_with(old_path, new_path)


def test_write_writes_using_entity(mocker, comms, ui, submission):
    spy = mocker.patch(PATCH_MLCUBE.format("Cube.write"))

    # Act
    submission.write(submission.cube.todict())

    # Assert
    spy.assert_called_once_with()


def test_upload_uploads_using_entity(mocker, comms, ui, submission):
    spy = mocker.patch(PATCH_MLCUBE.format("Cube.upload"))

    # Act
    submission.upload()

    # Assert
    spy.assert_called_once_with()
