import pytest
from unittest.mock import ANY, call

from medperf import config
from medperf.commands.mlcube import SubmitCube
from medperf.tests.utils import rand_l

PATCH_MLCUBE = "medperf.commands.mlcube.submit.{}"


@pytest.mark.parametrize("name", [None, "", "name"])
@pytest.mark.parametrize("mlc_file", [None, "", "mlc_file"])
@pytest.mark.parametrize("params_file", [None, "", "params_file"])
@pytest.mark.parametrize("add_file", [None, "", "add_file"])
def test_get_information_prompts_unassigned_fields(
    mocker, comms, ui, name, mlc_file, params_file, add_file
):
    # Arrange
    assign_val = "assign_val"
    submission = SubmitCube(comms, ui)
    submission.name = name
    submission.mlcube_file = mlc_file
    submission.params_file = params_file
    submission.additional_file = add_file
    mocker.patch.object(ui, "prompt", return_value=assign_val)

    # Act
    submission.get_information()

    # Assert
    if not name:
        assert submission.name == assign_val
    else:
        assert submission.name == name
    if not mlc_file:
        assert submission.mlcube_file == assign_val
    else:
        assert submission.mlcube_file == mlc_file
    if not params_file:
        assert submission.params_file == assign_val
    else:
        assert submission.params_file == params_file
    if not add_file:
        assert submission.additional_file == assign_val
    else:
        assert submission.additional_file == add_file


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
    submission = SubmitCube(comms, ui)
    submission.name = name[0]
    submission.mlcube_file = mlc_file[0]
    submission.params_file = params_file[0]
    submission.additional_file = add_file[0]
    should_pass = all([name[1], mlc_file[1], params_file[1], add_file[1]])

    # Act
    valid = submission.is_valid()

    # Assert
    assert valid == should_pass


@pytest.mark.parametrize("add_file", rand_l(1, 500, 2))
def test_get_hash_gets_additional_file(mocker, comms, ui, add_file):
    # Arrange
    add_file = str(add_file)
    submission = SubmitCube(comms, ui)
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
    submission = SubmitCube(comms, ui)
    spy_todict = mocker.patch.object(submission, "todict", return_value=mock_body)
    spy_upload = mocker.patch.object(comms, "upload_mlcube", return_value=1)

    # Act
    submission.submit()

    # Assert
    spy_todict.assert_called_once()
    spy_upload.assert_called_once_with(mock_body)

