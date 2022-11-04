import os
from medperf.tests.mocks.requests import cube_metadata_generator
from medperf.utils import storage_path
import pytest

import medperf.config as config
from medperf.commands.mlcube.submit import SubmitCube

PATCH_MLCUBE = "medperf.commands.mlcube.submit.{}"


@pytest.fixture
def cube(mocker):
    mocker.patch(PATCH_MLCUBE.format("Cube.download"))
    mocker.patch(PATCH_MLCUBE.format("Cube.get_local_hashes"))
    mocker.patch(PATCH_MLCUBE.format("Cube.is_valid"), return_value=True)
    mocker.patch(PATCH_MLCUBE.format("Cube.upload"))
    mocker.patch(PATCH_MLCUBE.format("Cube.write"))


@pytest.mark.parametrize("name", [("", False), ("valid", True), ("1" * 20, False)])
@pytest.mark.parametrize(
    "mlc_file",
    [
        ("", False),
        ("invalid", False),
        ("https://google.com", False),
        (config.git_file_domain + "/mlcube.yaml", True),
    ],
)
@pytest.mark.parametrize(
    "params_file",
    [
        ("invalid", False),
        ("https://google.com", False),
        (config.git_file_domain + "/parameters.yaml", True),
    ],
)
@pytest.mark.parametrize("add_file", [("invalid", False), ("https://google.com", True)])
@pytest.mark.parametrize("img_file", [("invalid", False), ("https://google.com", True)])
def test_is_valid_passes_valid_fields(
    mocker, comms, ui, name, mlc_file, params_file, add_file, img_file
):
    # Arrange
    submit_info = {
        "name": name[0],
        "mlcube_file": mlc_file[0],
        "params_file": params_file[0],
        "additional_files_tarball_url": add_file[0],
        "additional_files_tarball_hash": "",
        "image_tarball_url": img_file[0],
        "image_tarball_hash": "",
    }
    submission = SubmitCube(submit_info)
    should_pass = all([name[1], mlc_file[1], params_file[1], add_file[1], img_file[1]])

    # Act
    valid = submission.is_valid()

    # Assert
    assert valid == should_pass


def test_run_runs_expected_flow(mocker, comms, ui, cube):
    # Arrange
    mock_body = cube_metadata_generator()(1)
    # Arrange
    submit_info = {
        "name": "",
        "mlcube_file": "",
        "params_file": "",
        "additional_files_tarball_url": "",
        "additional_files_tarball_hash": "",
        "image_tarball_url": "",
        "image_tarball_hash": "",
    }
    spy_isval = mocker.patch(
        PATCH_MLCUBE.format("SubmitCube.is_valid"), return_value=True
    )
    spy_download = mocker.patch(PATCH_MLCUBE.format("SubmitCube.download"))
    spy_cube_upload = mocker.patch(
        PATCH_MLCUBE.format("SubmitCube.upload"), return_value=mock_body
    )
    spy_toper = mocker.patch(PATCH_MLCUBE.format("SubmitCube.to_permanent_path"))
    spy_write = mocker.patch(PATCH_MLCUBE.format("SubmitCube.write"))

    # Act
    SubmitCube.run(submit_info)

    # Assert
    spy_isval.assert_called_once()
    spy_download.assert_called_once()
    spy_cube_upload.assert_called_once()
    spy_toper.assert_called_once_with(mock_body["id"])
    spy_write.assert_called_once_with(mock_body)


@pytest.mark.parametrize("uid", [858, 2770, 2052])
def test_to_permanent_path_renames_correctly(mocker, comms, ui, cube, uid):
    # Arrange
    submit_info = {
        "name": "",
        "mlcube_file": "",
        "params_file": "",
        "additional_files_tarball_url": "",
        "additional_files_tarball_hash": "",
        "image_tarball_url": "",
        "image_tarball_hash": "",
    }
    submission = SubmitCube(submit_info)
    spy = mocker.patch("os.rename")
    mocker.patch("os.path.exists", return_value=False)
    old_path = os.path.join(
        storage_path(config.cubes_storage), config.cube_submission_id
    )
    new_path = os.path.join(storage_path(config.cubes_storage), str(uid))

    # Act
    submission.to_permanent_path(uid)

    # Assert
    spy.assert_called_once_with(old_path, new_path)


def test_write_writes_using_entity(mocker, comms, ui, cube):
    submit_info = {
        "name": "",
        "mlcube_file": "",
        "params_file": "",
        "additional_files_tarball_url": "",
        "additional_files_tarball_hash": "",
        "image_tarball_url": "",
        "image_tarball_hash": "",
    }
    submission = SubmitCube(submit_info)
    spy = mocker.patch(PATCH_MLCUBE.format("Cube.write"))
    mockdata = submission.todict()

    # Act
    submission.write(mockdata)

    # Assert
    spy.assert_called_once_with()


def test_upload_uploads_using_entity(mocker, comms, ui, cube):
    submit_info = {
        "name": "",
        "mlcube_file": "",
        "params_file": "",
        "additional_files_tarball_url": "",
        "additional_files_tarball_hash": "",
        "image_tarball_url": "",
        "image_tarball_hash": "",
    }
    submission = SubmitCube(submit_info)
    spy = mocker.patch(PATCH_MLCUBE.format("Cube.upload"))

    # Act
    submission.upload()

    # Assert
    spy.assert_called_once_with()


def test_download_executes_expected_commands(mocker, comms, ui, cube):
    submit_info = {
        "name": "",
        "mlcube_file": "",
        "params_file": "",
        "additional_files_tarball_url": "",
        "additional_files_tarball_hash": "",
        "image_tarball_url": "",
        "image_tarball_hash": "",
    }
    submission = SubmitCube(submit_info)
    down_spy = mocker.patch(PATCH_MLCUBE.format("Cube.download"))
    is_valid_spy = mocker.patch(PATCH_MLCUBE.format("Cube.is_valid"))

    # Act
    submission.download()

    # Assert
    down_spy.assert_called_once_with()
    is_valid_spy.assert_called_once_with()
