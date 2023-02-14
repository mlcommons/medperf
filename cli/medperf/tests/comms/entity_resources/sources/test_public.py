from medperf.tests.mocks import MockResponse
from medperf.comms.entity_resources.sources.public import PublicSource
import medperf.config as config
import pytest
from medperf.exceptions import CommunicationRetrievalError

PATCH_PUBLIC = "medperf.comms.entity_resources.sources.public.{}"
url = "https://mock.com"


def test_download_works_as_expected(mocker, fs):
    # Arrange
    filename = "filename"
    res = MockResponse({}, 200)
    iter_spy = mocker.patch.object(res, "iter_content", return_value=[b"some", b"text"])
    get_spy = mocker.patch(PATCH_PUBLIC.format("requests.get"), return_value=res)

    # Act
    PublicSource().download(url, filename)

    # Assert
    assert open(filename).read() == "sometext"
    get_spy.assert_called_once_with(url, stream=True)
    iter_spy.assert_called_once_with(chunk_size=config.ddl_stream_chunk_size)


def test_download_raises_for_failed_request(mocker):
    # Arrange
    filename = "filename"
    res = MockResponse({}, 404)
    mocker.patch(PATCH_PUBLIC.format("requests.get"), return_value=res)

    # Act & Assert
    with pytest.raises(CommunicationRetrievalError):
        PublicSource().download(url, filename)
