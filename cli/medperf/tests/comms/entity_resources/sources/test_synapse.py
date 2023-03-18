from medperf.comms.entity_resources.sources.synapse import SynapseSource
import pytest
import os
from medperf.exceptions import (
    CommunicationAuthenticationError,
    CommunicationRetrievalError,
)
from synapseclient.core.exceptions import (
    SynapseNoCredentialsError,
    SynapseHTTPError,
    SynapseUnmetAccessRestrictions,
)
import synapseclient


class MockSynapseFile:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def synapse_client(mocker):
    mock = mocker.create_autospec(synapseclient.Synapse)
    mocker.patch.object(synapseclient, "Synapse", return_value=mock)


def test_download_works_as_expected(mocker, fs, synapse_client):
    # Arrange
    outpath = "path/to/out.tar.gz"
    contents = "contents"
    syn_id = "syn535353"
    synapse_source = SynapseSource()

    def __side_effect(resource_identifier, downloadLocation):
        resource_name = "name we can't know"
        fs.create_file(os.path.join(downloadLocation, resource_name), contents=contents)
        return MockSynapseFile(resource_name)

    get_spy = mocker.patch.object(
        synapse_source.client, "get", side_effect=__side_effect
    )

    # Act
    synapse_source.download(syn_id, outpath)

    # Assert
    get_spy.assert_called_once_with(syn_id, downloadLocation=os.path.dirname(outpath))
    assert open(outpath).read() == contents


@pytest.mark.parametrize(
    "exception", [SynapseHTTPError, SynapseUnmetAccessRestrictions]
)
def test_download_raises_for_failed_request(mocker, fs, synapse_client, exception):
    # Arrange
    outpath = "path/to/out.tar.gz"
    syn_id = "syn535353"
    synapse_source = SynapseSource()

    def __side_effect(resource_identifier, downloadLocation):
        raise exception

    mocker.patch.object(synapse_source.client, "get", side_effect=__side_effect)

    # Act & Assert
    with pytest.raises(CommunicationRetrievalError):
        synapse_source.download(syn_id, outpath)


def test_download_raises_for_silently_failed_request(mocker, fs, synapse_client):
    # Arrange
    outpath = "path/to/out.tar.gz"
    syn_id = "syn535353"
    synapse_source = SynapseSource()

    def __side_effect(resource_identifier, downloadLocation):
        resource_name = "name we can't know"
        return MockSynapseFile(resource_name)

    mocker.patch.object(synapse_source.client, "get", side_effect=__side_effect)

    # Act & Assert
    with pytest.raises(CommunicationRetrievalError):
        synapse_source.download(syn_id, outpath)


def test_authenticate_calls_login(mocker, synapse_client):
    # Arrange
    synapse_source = SynapseSource()
    spy = mocker.patch.object(synapse_source.client, "login")

    # Act
    synapse_source.authenticate()

    # Assert
    spy.assert_called_once()


def test_authenticate_fails_for_failing_login(mocker, synapse_client):
    # Arrange
    synapse_source = SynapseSource()

    def __side_effect(**kwargs):
        raise SynapseNoCredentialsError

    mocker.patch.object(synapse_source.client, "login", side_effect=__side_effect)

    # Act & Assert
    with pytest.raises(CommunicationAuthenticationError):
        synapse_source.authenticate()
