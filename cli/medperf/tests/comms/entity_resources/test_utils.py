from medperf.exceptions import InvalidArgumentError
import pytest
from medperf.comms.entity_resources import sources, utils


# prefixes
DIRECT = sources.DirectLinkSource.prefix
SYNAPSE = sources.SynapseSource.prefix


@pytest.mark.parametrize(
    "resource,source_class",
    [
        ("https://url2.com", sources.DirectLinkSource),
        (f"{DIRECT}https://url1.com", sources.DirectLinkSource),
        (f"{SYNAPSE}syn532035", sources.SynapseSource),
    ],
)
def test_download_resource_runs_for_valid_input(mocker, resource, source_class):
    # Arrange
    output_path = "out"
    resource_identifier = resource.replace(source_class.prefix, "")
    auth_spy = mocker.patch.object(source_class, "authenticate")
    download_spy = mocker.patch.object(source_class, "download")

    # Act
    utils.download_resource(resource, output_path)

    # Assert
    auth_spy.assert_called_once()
    download_spy.assert_called_once_with(resource_identifier, output_path)


@pytest.mark.parametrize(
    "resource",
    [
        "some string",
        f"{DIRECT}some string",
        f"{SYNAPSE}https://url.com",
        f"{DIRECT}syn4444",
        f"{SYNAPSE}syn353tt",
    ],
)
def test_download_resource_fails_for_invalid_input(mocker, resource):
    # Act & Assert
    with pytest.raises(InvalidArgumentError):
        utils.download_resource(resource, "whatever")
