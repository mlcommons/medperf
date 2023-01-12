import pytest
from medperf.commands.auth import Login

PATCH_LOGIN = "medperf.commands.auth.login.{}"


@pytest.fixture(params=["token123"])
def comms(mocker, request, comms):
    mocker.patch.object(comms, "login")
    mocker.patch("os.remove")
    mocker.patch("os.chmod")
    comms.token = request.param
    return comms


def test_runs_comms_login(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "login")
    mocker.patch(PATCH_LOGIN.format("set_credentials"))
    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("profile", ["default", "test", "user"])
def test_assigns_credentials_to_profile(mocker, profile, comms, ui):
    # Arrange
    spy = mocker.patch(PATCH_LOGIN.format("set_credentials"))

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once_with(comms.token)
