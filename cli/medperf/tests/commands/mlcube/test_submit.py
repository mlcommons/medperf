import pytest

import medperf.config as config
from medperf.commands.mlcube.submit import SubmitCube

PATCH_MLCUBE = "medperf.commands.mlcube.submit.{}"


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


def test_run_downloads_cube(mocker, comms, ui):
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
    spy_todict = mocker.patch(PATCH_MLCUBE.format("SubmitCube.is_valid"), return_value=True)
    spy_download = mocker.patch(PATCH_MLCUBE.format("Cube.download"))

    # Act
    SubmitCube.run(submit_info)

    # Assert
    spy_todict.assert_called_once()
    spy_download.assert_called_once()


def test_submit_uploads_cube_data(mocker, comms, ui):
    # Arrange
    mock_body = {}
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
    spy_todict = mocker.patch.object(submission, "todict", return_value=mock_body)
    spy_upload = mocker.patch.object(comms, "upload_mlcube", return_value=1)

    # Act
    submission.submit()

    # Assert
    spy_todict.assert_called_once()
    spy_upload.assert_called_once_with(mock_body)
