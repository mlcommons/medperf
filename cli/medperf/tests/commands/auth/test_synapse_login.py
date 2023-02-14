import pytest
from medperf.commands.auth import SynapseLogin
import synapseclient
from synapseclient.core.exceptions import SynapseError
from medperf.exceptions import CommunicationAuthenticationError

PATCH_LOGIN = "medperf.commands.auth.synapse_login.{}"


@pytest.fixture
def synapse_client(mocker):
    mock = mocker.create_autospec(synapseclient.Synapse)
    mocker.patch.object(synapseclient, "Synapse", return_value=mock)
    return mock


def test_run_calls_synapse_login(mocker, synapse_client, ui):
    # Arrange
    spy = mocker.patch.object(synapse_client, "login")

    # Act
    SynapseLogin.run("usr", "pwd")

    # Assert
    spy.assert_called_once_with("usr", "pwd", rememberMe=True)


def test_run_fails_if_error(mocker, synapse_client, ui):
    # Arrange
    def __side_effect(*args, **kwargs):
        raise SynapseError

    mocker.patch.object(synapse_client, "login", side_effect=__side_effect)

    # Act & Assert
    with pytest.raises(CommunicationAuthenticationError):
        SynapseLogin.run("usr", "pwd")
