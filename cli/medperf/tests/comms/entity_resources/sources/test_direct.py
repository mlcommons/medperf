from medperf.tests.mocks import MockResponse
from medperf.comms.entity_resources.sources.direct import DirectLinkSource
from medperf import settings
import pytest
from medperf.exceptions import CommunicationRetrievalError

PATCH_DIRECT = "medperf.comms.entity_resources.sources.direct.{}"
url = "https://mock.com"


def test_download_works_as_expected(mocker, fs):
    # Arrange
    filename = "filename"
    res = MockResponse({}, 200)
    iter_spy = mocker.patch.object(res, "iter_content", return_value=[b"some", b"text"])
    get_spy = mocker.patch(PATCH_DIRECT.format("requests.get"), return_value=res)

    # Act
    DirectLinkSource().download(url, filename)

    # Assert
    assert open(filename).read() == "sometext"
    get_spy.assert_called_once_with(url, stream=True)
    iter_spy.assert_called_once_with(chunk_size=settings.ddl_stream_chunk_size)


def test_download_raises_for_failed_request_after_multiple_attempts(mocker):
    # Arrange
    filename = "filename"
    res = MockResponse({}, 404)
    spy = mocker.patch(PATCH_DIRECT.format("requests.get"), return_value=res)

    # Act & Assert
    with pytest.raises(CommunicationRetrievalError):
        DirectLinkSource().download(url, filename)

    assert spy.call_count == settings.ddl_max_redownload_attempts
