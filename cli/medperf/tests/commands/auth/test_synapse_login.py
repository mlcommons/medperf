import pytest
from medperf.commands.auth.synapse_login import SynapseLogin
import synapseclient
from synapseclient.core.exceptions import SynapseAuthenticationError
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
        raise SynapseAuthenticationError

    mocker.patch.object(synapse_client, "login", side_effect=__side_effect)

    # Act & Assert
    with pytest.raises(CommunicationAuthenticationError):
        SynapseLogin.run(token="token")


def test_run_calls_the_correct_method(mocker, synapse_client, ui):
    # Arrange
    mocker.patch.object(ui, "prompt")
    token_spy = mocker.patch(PATCH_LOGIN.format("SynapseLogin.login_with_token"))

    # Act
    SynapseLogin.run()

    # Assert
    token_spy.assert_called_once()


def test_login_with_token_calls_synapse_login(mocker, synapse_client, ui):
    # Arrange
    spy = mocker.patch.object(synapse_client, "login")

    # Act
    SynapseLogin.login_with_token("token")

    # Assert
    spy.assert_called_once_with(authToken="token")
