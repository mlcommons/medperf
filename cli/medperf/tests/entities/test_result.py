import os
from medperf.tests.mocks.requests import result_dict
import pytest
from unittest.mock import MagicMock, call, ANY

from medperf.entities.result import Result
from medperf.comms.interface import Comms
from medperf import config

PATCH_RESULT = "medperf.entities.result.{}"
MOCK_RESULTS_CONTENT = result_dict({"id": "1", "results": {}})


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    config.comms = comms
    return comms


@pytest.fixture
def result(mocker):
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.safe_load", return_value=MOCK_RESULTS_CONTENT)
    result = Result.from_entities_uids(1, 1, 1)
    return result


@pytest.mark.parametrize("results_path", [".", "~/.medperf/results/1"])
def test_from_entities_uids_open_results_info_file(mocker, results_path):
    # Arrange
    open_spy = mocker.patch("builtins.open", MagicMock())
    yaml_spy = mocker.patch("yaml.safe_load", return_value=MOCK_RESULTS_CONTENT)
    mocker.patch(PATCH_RESULT.format("results_path"), return_value=results_path)
    exp_path = os.path.join(results_path, config.results_info_file)

    # Act
    Result.from_entities_uids(1, 1, 1)

    # Assert
    # get_spy.assert_called_once()
    open_spy.assert_called_once_with(exp_path, "r")
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
    spy = mocker.spy(Result, "from_entities_uids")
    mocker.patch("os.path.join", return_value=mock_path)

    # Act
    Result.all()

    # Assert
    spy.assert_has_calls([call(b_id, m_id, d_id)])


@pytest.mark.parametrize("uid", [349, 2, 84])
def test_get_retrieves_results_from_comms(mocker, comms, uid):
    # Arrange
    uid = 0
    spy = mocker.patch.object(comms, "get_result", return_value=MOCK_RESULTS_CONTENT)
    mocker.patch(PATCH_RESULT.format("Result.all"), return_value=[])
    mocker.patch(PATCH_RESULT.format("Result.write"))

    # Act
    Result.get(uid)

    # Assert
    spy.assert_called_once_with(uid)


def test_todict_returns_expected_keys(mocker, result):
    # Arrange
    expected_keys = set(MOCK_RESULTS_CONTENT.keys())

    # Act
    result_dict = result.todict()

    # Assert
    assert set(result_dict.keys()) == expected_keys


def test_upload_calls_server_method(mocker, result, comms):
    # Arrange
    spy = mocker.patch.object(comms, "upload_results")
    mocker.patch(
        PATCH_RESULT.format("Result.todict"), return_value=MOCK_RESULTS_CONTENT
    )
    mocker.patch(PATCH_RESULT.format("Result.write"))

    # Act
    result.upload()

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("write_access", [True, False])
def test_set_results_writes_results_contents_to_file(mocker, result, write_access):
    # Arrange
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.access", return_value=write_access)
    mocker.patch("os.remove")
    open_spy = mocker.patch("builtins.open", MagicMock())
    yaml_spy = mocker.patch("yaml.dump")
    mocker.patch("os.makedirs")

    # Act
    result.write()

    # arrange
    open_spy.assert_called_once_with(result.path, "w")
    yaml_spy.assert_called_once_with(result.todict(), ANY)


@pytest.mark.parametrize("write_access", [True, False])
def test_set_results_deletes_file_if_inaccessible(mocker, result, write_access):
    # Arrange
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
        spy.assert_called_once_with(result.path)
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


def test_from_entities_uids_calls_local_dict_with_correct_entities_order(mocker):
    # Arrange
    bmk, model, data = "bmk", "model", "data"
    spy = mocker.patch(
        PATCH_RESULT.format("Result._Result__get_local_dict"),
        return_value=result_dict(),
    )

    # Act
    Result.from_entities_uids(bmk, model, data)

    # Assert
    spy.assert_called_once_with(bmk, model, data)


def test_get_local_dict_calls_result_path_with_correct_entities_order(mocker):
    # Arrange
    bmk, model, data = "bmk", "model", "data"
    spy = mocker.patch(PATCH_RESULT.format("results_path"))
    mocker.patch(PATCH_RESULT.format("os.path.join"))
    mocker.patch(PATCH_RESULT.format("yaml.safe_load"), return_value=result_dict())
    mocker.patch(PATCH_RESULT.format("Result.__init__"), return_value=None)
    mocker.patch("builtins.open")

    # Act
    Result.from_entities_uids(bmk, model, data)

    # Assert
    spy.assert_called_once_with(bmk, model, data)
