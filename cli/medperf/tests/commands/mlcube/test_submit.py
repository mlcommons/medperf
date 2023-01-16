import os
from medperf.tests.mocks.requests import cube_metadata_generator
from medperf.utils import storage_path
import pytest

import medperf.config as config
from medperf.commands.mlcube.submit import SubmitCube

PATCH_MLCUBE = "medperf.commands.mlcube.submit.{}"

SUBMIT_INFO = {
    "name": "",
    "mlcube_file": "",
    "params_file": "",
    "additional_files_tarball_url": "",
    "additional_files_tarball_hash": "",
    "image_tarball_url": "",
    "image_tarball_hash": "",
    "mlcube_hash": "",
    "parameters_hash": "",
}


@pytest.fixture
def cube(mocker):
    mocker.patch(PATCH_MLCUBE.format("Cube.download"))
    mocker.patch(PATCH_MLCUBE.format("Cube.get_local_hashes"))
    mocker.patch(PATCH_MLCUBE.format("Cube.is_valid"), return_value=True)
    mocker.patch(PATCH_MLCUBE.format("Cube.upload"))
    mocker.patch(PATCH_MLCUBE.format("Cube.write"))


@pytest.mark.parametrize(
    "name,mlc_file,params_file,add_file,img_file,should_pass",
    [
        # Valid minimal submission
        ("valid", "https://test.test/mlcube.yaml", "", "", "", True,),
        # Invalid empty name
        (
            "",
            "https://test.test/mlcube.yaml",
            "https://test.test/parameters.yaml",
            "",
            "",
            False,
        ),
        # Invalid name length
        (
            "1" * 20,
            "https://test.test/mlcube.yaml",
            "https://test.test/parameters.yaml",
            "",
            "",
            False,
        ),
        # Invalid empty mlcube file
        ("valid", "", "https://test.test/parameters.yaml", "", "", False),
        # Invalid mlcube url
        (
            "valid",
            "https://test.test",
            "https://test.test/parameters.yaml",
            "",
            "",
            False,
        ),
        # Invalid parameters url
        ("valid", "https://test.test/mlcube.yaml", "https://test.test", "", "", False),
        # Invalid additional files string
        (
            "valid",
            "https://test.test/mlcube.yaml",
            "https://test.test/parameters.yaml",
            "invalid",
            "",
            False,
        ),
        # Invalid image file string
        (
            "valid",
            "https://test.test/mlcube.yaml",
            "https://test.test/parameters.yaml",
            "",
            "invalid",
            False,
        ),
        # Valid complete submission
        (
            "valid",
            "https://test.test/mlcube.yaml",
            "https://test.test/parameters.yaml",
            "https://test.test",
            "https://test.test",
            True,
        ),
    ],
)
def test_is_valid_passes_valid_fields(
    mocker, comms, ui, name, mlc_file, params_file, add_file, img_file, should_pass
):
    # Arrange
    submit_info = {
        "name": name,
        "mlcube_file": mlc_file,
        "params_file": params_file,
        "additional_files_tarball_url": add_file,
        "additional_files_tarball_hash": "",
        "image_tarball_url": img_file,
        "image_tarball_hash": "",
        "mlcube_hash": "",
        "parameters_hash": "",
    }
    submission = SubmitCube(submit_info)

    # Act
    valid = submission.is_valid()

    # Assert
    assert valid == should_pass


def test_run_runs_expected_flow(mocker, comms, ui, cube):
    # Arrange
    mock_body = cube_metadata_generator()(1)
    # Arrange
    submit_info = SUBMIT_INFO
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
    spy_toper.assert_called_once_with(mock_body)
    spy_write.assert_called_once_with(mock_body)


@pytest.mark.parametrize("uid", [858, 2770, 2052])
def test_to_permanent_path_renames_correctly(mocker, comms, ui, cube, uid):
    # Arrange
    submit_info = SUBMIT_INFO
    mock_body = cube_metadata_generator()(uid)
    submission = SubmitCube(submit_info)
    spy = mocker.patch("os.rename")
    mocker.patch("os.path.exists", return_value=False)
    old_path = os.path.join(storage_path(config.cubes_storage), mock_body["name"])
    new_path = os.path.join(storage_path(config.cubes_storage), str(uid))

    # Act
    submission.to_permanent_path(mock_body)

    # Assert
    spy.assert_called_once_with(old_path, new_path)


def test_write_writes_using_entity(mocker, comms, ui, cube):
    submit_info = SUBMIT_INFO
    submission = SubmitCube(submit_info)
    spy = mocker.patch(PATCH_MLCUBE.format("Cube.write"))
    mockdata = submission.todict()

    # Act
    submission.write(mockdata)

    # Assert
    spy.assert_called_once_with()


def test_upload_uploads_using_entity(mocker, comms, ui, cube):
    submit_info = SUBMIT_INFO
    submission = SubmitCube(submit_info)
    spy = mocker.patch(PATCH_MLCUBE.format("Cube.upload"))

    # Act
    submission.upload()

    # Assert
    spy.assert_called_once_with()


def test_download_executes_expected_commands(mocker, comms, ui, cube):
    submit_info = SUBMIT_INFO
    submission = SubmitCube(submit_info)
    down_spy = mocker.patch(PATCH_MLCUBE.format("Cube.download"))
    is_valid_spy = mocker.patch(PATCH_MLCUBE.format("Cube.is_valid"))

    # Act
    submission.download()

    # Assert
    down_spy.assert_called_once_with()
    is_valid_spy.assert_called_once_with()
