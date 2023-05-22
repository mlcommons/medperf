import os
from medperf.exceptions import InvalidArgumentError, InvalidEntityError
from medperf.tests.utils import calculate_fake_file_hash
import pytest
from medperf.comms.entity_resources import sources, utils
import synapseclient

# prefixes
DIRECT = sources.DirectLinkSource.prefix
SYNAPSE = sources.SynapseSource.prefix


DOWNLOADED_FILE_CONTENTS = "some contents"


@pytest.fixture(autouse=True)
def setup_download_side_effect(mocker, fs):
    def download_side_effect(identifier, outpath):
        fs.create_file(outpath, contents=DOWNLOADED_FILE_CONTENTS)

    mocker.patch.object(
        sources.DirectLinkSource, "download", side_effect=download_side_effect
    )
    mocker.patch.object(
        sources.SynapseSource, "download", side_effect=download_side_effect
    )


class TestWithNoHash:
    @pytest.fixture(autouse=True)
    def synapse_client(self, mocker):
        mock = mocker.create_autospec(synapseclient.Synapse)
        mocker.patch.object(synapseclient, "Synapse", return_value=mock)

    @pytest.mark.parametrize(
        "resource,source_class",
        [
            ("https://url2.com", sources.DirectLinkSource),
            (f"{DIRECT}https://url1.com", sources.DirectLinkSource),
            (f"{SYNAPSE}syn532035", sources.SynapseSource),
        ],
    )
    def test_download_resource_runs_for_valid_input(
        self, mocker, resource, source_class, fs
    ):
        # Arrange
        output_path = "out"
        auth_spy = mocker.patch.object(source_class, "authenticate")

        # Act
        utils.download_resource(resource, output_path)

        # Assert
        auth_spy.assert_called_once()
        assert os.path.exists(output_path)

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
    def test_download_resource_fails_for_invalid_input(self, mocker, resource):
        # Act & Assert
        with pytest.raises(InvalidArgumentError):
            utils.download_resource(resource, "whatever")


# From here, we will be using only the direct link source
class TestWithHash:
    def test_download_with_invalid_hash(self, fs):
        # Arrange
        output_path = "out"
        expected_hash = "some unmatching hash"

        # Act & Assert
        with pytest.raises(InvalidEntityError):
            utils.download_resource("https://url.com", output_path, expected_hash)

    def test_download_with_valid_hash(self, fs):
        # Arrange
        output_path = "out"

        expected_hash = calculate_fake_file_hash(fs, DOWNLOADED_FILE_CONTENTS)

        # Act
        utils.download_resource("https://url.com", output_path, expected_hash)

        # Assert
        assert open(output_path).read() == DOWNLOADED_FILE_CONTENTS
