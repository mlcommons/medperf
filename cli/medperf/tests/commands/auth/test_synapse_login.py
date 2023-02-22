import pytest
from medperf.commands.auth import SynapseLogin
import synapseclient
from synapseclient.core.exceptions import SynapseError
from medperf.exceptions import CommunicationAuthenticationError, InvalidArgumentError

PATCH_LOGIN = "medperf.commands.auth.synapse_login.{}"


@pytest.fixture
def synapse_client(mocker):
    mock = mocker.create_autospec(synapseclient.Synapse)
    mocker.patch.object(synapseclient, "Synapse", return_value=mock)
    return mock


def test_run_fails_if_error(mocker, synapse_client, ui):
    # Arrange
    def __side_effect(*args, **kwargs):
        raise SynapseError

    mocker.patch.object(synapse_client, "login", side_effect=__side_effect)

    # Act & Assert
    with pytest.raises(CommunicationAuthenticationError):
        SynapseLogin.run("usr", "pwd")

    with pytest.raises(CommunicationAuthenticationError):
        SynapseLogin.run(token="token")


def test_run_fails_if_invalid_args(mocker, synapse_client, ui):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        SynapseLogin.run("usr", "pwd", "token")

    with pytest.raises(InvalidArgumentError):
        SynapseLogin.run("usr", None, "token")


@pytest.mark.parametrize("user_input", ["1", "2"])
def test_run_calls_the_correct_method(mocker, synapse_client, ui, user_input):
    # Arrange
    mocker.patch.object(ui, "prompt", return_value=user_input)
    token_spy = mocker.patch(PATCH_LOGIN.format("SynapseLogin.login_with_token"))
    pwd_spy = mocker.patch(PATCH_LOGIN.format("SynapseLogin.login_with_password"))

    # Act
    SynapseLogin.run()

    # Assert
    if user_input == "1":
        token_spy.assert_called_once()
        pwd_spy.assert_not_called()
    else:
        token_spy.assert_not_called()
        pwd_spy.assert_called_once()


def test_login_with_password_calls_synapse_login(mocker, synapse_client, ui):
    # Arrange
    spy = mocker.patch.object(synapse_client, "login")

    # Act
    SynapseLogin.login_with_password("usr", "pwd")

    # Assert
    spy.assert_called_once_with("usr", "pwd", rememberMe=True)


def test_login_with_token_calls_synapse_login(mocker, synapse_client, ui):
    # Arrange
    spy = mocker.patch.object(synapse_client, "login")

    # Act
    SynapseLogin.login_with_token("token")

    # Assert
    spy.assert_called_once_with(authToken="token", rememberMe=True)
