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


@pytest.fixture(autouse=True)
def setup(mocker, fs):
    mocker.patch(PATCH_LOGIN.format("set_credentials"))
    mocker.patch(PATCH_LOGIN.format("set_current_user"))


def test_runs_comms_login(mocker, comms, ui, fs):
    # Arrange
    spy = mocker.patch.object(comms, "login")

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once()


def test_runs_comms_get_current_user(mocker, comms, ui, fs):
    # Arrange
    spy = mocker.patch.object(comms, "get_current_user")

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("profile", ["default", "test", "user"])
def test_assigns_credentials_to_profile(mocker, profile, comms, ui, fs):
    # Arrange
    spy = mocker.patch(PATCH_LOGIN.format("set_credentials"))

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once_with(comms.token)


@pytest.mark.parametrize("user", [{"id": 1}, {"id": 278}])
def test_assigns_user_to_profile(mocker, user, comms, ui, fs):
    # Arrange
    mocker.patch.object(comms, "get_current_user", return_value=user)
    spy = mocker.patch(PATCH_LOGIN.format("set_current_user"))

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once_with(user)
