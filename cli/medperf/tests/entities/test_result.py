import os
from medperf.tests.mocks.requests import result_dict
import pytest
from unittest.mock import MagicMock, ANY, mock_open

from medperf.entities.result import Result
from medperf import config

PATCH_RESULT = "medperf.entities.result.{}"
MOCK_RESULTS_CONTENT = result_dict({"id": "1", "results": {}})


@pytest.fixture
def basic_arrange(mocker):
    m = mock_open()
    mocker.patch("builtins.open", m, create=True)
    mocker.patch(
        PATCH_RESULT.format("yaml.safe_load"), return_value=MOCK_RESULTS_CONTENT
    )
    mocker.patch(PATCH_RESULT.format("os.path.exists"), return_value=True)
    return m


@pytest.fixture
def all_uids(mocker, basic_arrange, request):
    uids = request.param
    walk_out = iter([("", uids, [])])

    def mock_reg_file(ff):
        # Extract the uid of the opened registration file through the mocked object
        call_args = basic_arrange.call_args[0]
        # call args returns a tuple with the arguments called. Get the path
        path = call_args[0]
        # Get the uid by extracting second-to-last path element
        uid = path.split("/")[-2]
        # Assign the uid to the mocked registration dictionary
        reg = MOCK_RESULTS_CONTENT.copy()
        reg["generated_uid"] = uid
        return reg

    mocker.patch(PATCH_RESULT.format("yaml.safe_load"), side_effect=mock_reg_file)
    mocker.patch(PATCH_RESULT.format("os.walk"), return_value=walk_out)
    return uids


@pytest.fixture
def result(mocker, comms):
    mocker.patch.object(comms, "get_result", return_value=MOCK_RESULTS_CONTENT)
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.dump")
    mocker.patch("os.makedirs")
    result = Result.get(1)
    return result


@pytest.mark.parametrize("write_access", [True, False])
def test_set_results_writes_results_contents_to_file(mocker, result, write_access):
    # Arrange
    filepath = os.path.join(result.path, config.results_info_file)
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("os.access", return_value=write_access)
    mocker.patch("os.remove")
    open_spy = mocker.patch("builtins.open", MagicMock())
    yaml_spy = mocker.patch("yaml.dump")
    mocker.patch("os.makedirs")

    # Act
    result.write()

    # arrange
    open_spy.assert_called_once_with(filepath, "w")
    yaml_spy.assert_called_once_with(result.todict(), ANY)


@pytest.mark.parametrize("write_access", [True, False])
def test_set_results_deletes_file_if_inaccessible(mocker, result, write_access):
    # Arrange
    filepath = os.path.join(result.path, config.results_info_file)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.access", return_value=write_access)
    spy = mocker.patch("os.remove")
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.dump")
    mocker.patch("os.makedirs")
    # Act
    result.write()

    # arrange
    if not write_access:
        spy.assert_called_once_with(filepath)
    else:
        spy.assert_not_called()


@pytest.mark.parametrize("exists", [True, False])
def test_set_results_check_access_only_if_file_exists(mocker, result, exists):
    # Arrange
    mocker.patch("os.path.exists", return_value=exists)
    spy = mocker.patch("os.access")
    mocker.patch("os.remove")
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.dump")
    mocker.patch("os.makedirs")

    # Act
    result.write()

    # arrange
    if exists:
        spy.assert_called_once()
    else:
        spy.assert_not_called()
