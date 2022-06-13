import pytest
from unittest.mock import ANY

import medperf.config as config
from medperf.tests.utils import rand_l
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
def test_is_valid_passes_valid_fields(
    mocker, comms, ui, name, mlc_file, params_file, add_file
):
    # Arrange
    submit_info = {
        "name": name[0],
        "mlcube_file": mlc_file[0],
        "params_file": params_file[0],
        "additional_file": add_file[0],
        "additional_hash": "",
    }
    submission = SubmitCube(submit_info, comms, ui)
    should_pass = all([name[1], mlc_file[1], params_file[1], add_file[1]])

    # Act
    valid = submission.is_valid()

    # Assert
    assert valid == should_pass


@pytest.mark.parametrize("add_file", rand_l(1, 500, 2))
def test_get_hash_gets_additional_file(mocker, comms, ui, add_file):
    # Arrange
    add_file = str(add_file)
    submit_info = {
        "name": "",
        "mlcube_file": "",
        "params_file": "",
        "additional_file": "",
        "additional_hash": "",
    }
    submission = SubmitCube(submit_info, comms, ui)
    submission.additional_file = add_file
    spy = mocker.patch.object(comms, "get_cube_additional", return_value="")
    mocker.patch(PATCH_MLCUBE.format("get_file_sha1"), return_value="")

    # Act
    submission.get_hash()

    # Assert
    spy.assert_called_once_with(add_file, ANY)


def test_submit_uploads_cube_data(mocker, comms, ui):
    # Arrange
    mock_body = {}
    submit_info = {
        "name": "",
        "mlcube_file": "",
        "params_file": "",
        "additional_file": "",
        "additional_hash": "",
    }
    submission = SubmitCube(submit_info, comms, ui)
    spy_todict = mocker.patch.object(submission, "todict", return_value=mock_body)
    spy_upload = mocker.patch.object(comms, "upload_mlcube", return_value=1)

    # Act
    submission.submit()

    # Assert
    spy_todict.assert_called_once()
    spy_upload.assert_called_once_with(mock_body)
