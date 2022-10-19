import pytest
from unittest.mock import MagicMock, call, ANY

from medperf.entities.result import Result
from medperf.comms.interface import Comms
from medperf import config

PATCH_RESULT = "medperf.entities.result.{}"
MOCK_RESULTS_CONTENT = {"id": "1", "results": {}}


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    config.comms = comms
    return comms


@pytest.fixture
def result(mocker):
    mocker.patch(PATCH_RESULT.format("Result.get_results"))
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.safe_load", return_value={})
    result = Result(1, 1, 1)
    result.results = MOCK_RESULTS_CONTENT
    result.uid = result.results["id"]
    return result


@pytest.mark.parametrize(
    "results_path", ["./results.yaml", "~/.medperf/results/1/results.yaml"]
)
def test_results_looks_for_results_path_on_init(mocker, results_path):
    # Arrange
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.safe_load", return_value={})
    mocker.spy(Result, "get_results")
    mocker.patch(PATCH_RESULT.format("results_path"), return_value=results_path)

    # Act
    result = Result(1, 1, 1)

    # Assert
    assert result.path == results_path


@pytest.mark.parametrize(
    "results_path", ["./results.yaml", "~/.medperf/results/1/results.yaml"]
)
def test_results_open_results_file_on_init(mocker, results_path):
    # Arrange
    open_spy = mocker.patch("builtins.open", MagicMock())
    yaml_spy = mocker.patch("yaml.safe_load", return_value={})
    get_spy = mocker.spy(Result, "get_results")
    mocker.patch(PATCH_RESULT.format("results_path"), return_value=results_path)

    # Act
    Result(1, 1, 1)

    # Assert
    get_spy.assert_called_once()
    open_spy.assert_called_once_with(results_path, "r")
    yaml_spy.assert_called_once()


def test_all_gets_results_ids(mocker, ui):
    # Arrange
    spy = mocker.patch(PATCH_RESULT.format("results_ids"), return_value=[])

    # Act
    Result.all()

    # Assert
    spy.assert_called_once()


def test_all_creates_result_objects_with_correct_info(
    mocker, result, ui,
):
    # Arrange
    mock_path = "results_filepath"
    result_ids = ("b_id", "m_id", "d_id")
    b_id, m_id, d_id = result_ids
    mocker.patch(PATCH_RESULT.format("results_ids"), return_value=[result_ids])
    spy = mocker.spy(Result, "__init__")
    mocker.patch("os.path.join", return_value=mock_path)

    # Act
    Result.all()

    # Assert
    spy.assert_has_calls([call(mocker.ANY, b_id, d_id, m_id)])


@pytest.mark.parametrize("uid", [349, 2, 84])
def test_get_retrieves_results_from_comms(mocker, comms, uid):
    # Arrange
    uid = 0
    result_dict = {"benchmark": 0, "dataset": 0, "model": 0, "results": {}, "uid": uid}
    spy = mocker.patch.object(comms, "get_result", return_value=result_dict)
    mocker.patch(PATCH_RESULT.format("Result.all"), return_value=[])

    # Act
    Result.get(uid)

    # Assert
    spy.assert_called_once_with(uid)


def test_todict_returns_expected_keys(mocker, result):
    # Arrange
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.safe_load", return_value={})
    expected_keys = {
        "name",
        "results",
        "metadata",
        "approval_status",
        "benchmark",
        "model",
        "dataset",
    }

    # Act
    result_dict = result.todict()

    # Assert
    assert set(result_dict.keys()) == expected_keys


def test_upload_calls_server_method(mocker, result, comms):
    # Arrange
    spy = mocker.patch.object(comms, "upload_results")
    mocker.patch(PATCH_RESULT.format("Result.todict"), return_value={})
    mocker.patch(PATCH_RESULT.format("Result.set_results"))

    # Act
    result.upload()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("write_access", [True, False])
def test_set_results_writes_results_contents_to_file(mocker, result, write_access):
    # Arrange
    mocker.patch("os.access", return_value=write_access)
    mocker.patch("os.remove")
    open_spy = mocker.patch("builtins.open", MagicMock())
    yaml_spy = mocker.patch("yaml.dump")

    # Act
    result.set_results()

    # arrange
    open_spy.assert_called_once_with(result.path, "w")
    yaml_spy.assert_called_once_with(result.results, ANY)


@pytest.mark.parametrize("write_access", [True, False])
def test_set_results_deletes_file_if_inaccessible(mocker, result, write_access):
    # Arrange
    mocker.patch("os.access", return_value=write_access)
    spy = mocker.patch("os.remove")
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.dump")

    # Act
    result.set_results()

    # arrange
    if not write_access:
        spy.assert_called_once_with(result.path)
    else:
        spy.assert_not_called()
