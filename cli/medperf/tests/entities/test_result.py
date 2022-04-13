import pytest
from unittest.mock import MagicMock, call, ANY

from medperf.entities.result import Result

PATCH_RESULT = "medperf.entities.result.{}"
MOCK_RESULTS_CONTENT = {"id": "1", "results": {}}


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
    result = Result(1, 1, 1)

    # Assert
    get_spy.assert_called_once()
    open_spy.assert_called_once_with(results_path, "r")
    yaml_spy.assert_called_once()


def test_all_gets_results_ids(mocker, ui):
    # Arrange
    spy = mocker.patch(PATCH_RESULT.format("results_ids"), return_value=[])

    # Act
    Result.all(ui)

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
    results = Result.all(ui)

    # Assert
    spy.assert_has_calls([call(mocker.ANY, b_id, d_id, m_id)])


@pytest.mark.parametrize(
    "results_path", ["./results.yaml", "~/.medperf/results/1/results.yaml"]
)
def test_todict_opens_results_file_as_yaml(mocker, result, results_path):
    # Arrange
    open_spy = mocker.patch("builtins.open", MagicMock())
    yaml_spy = mocker.patch("yaml.safe_load", return_value={})
    mocker.patch(PATCH_RESULT.format("results_path"), return_value=results_path)
    result = Result(1, 1, 1)

    # Act
    result.todict()

    # Assert
    open_spy.assert_called_once_with(results_path, "r")
    yaml_spy.assert_called_once()


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


def test_request_approval_skips_if_already_approved(mocker, result, ui):
    # Arrange
    spy = mocker.patch(PATCH_RESULT.format("approval_prompt"))
    result.status = "APPROVED"

    # Act
    result.request_approval(ui)

    # Assert
    spy.assert_not_called()


@pytest.mark.parametrize("exp_approved", [True, False])
def test_request_approval_returns_user_approval(mocker, result, ui, exp_approved):
    # Arrange
    mocker.patch("typer.echo")
    mocker.patch(PATCH_RESULT.format("dict_pretty_print"))
    mocker.patch(PATCH_RESULT.format("Result.todict"), return_value={})
    mocker.patch(PATCH_RESULT.format("approval_prompt"), return_value=exp_approved)

    # Act
    approved = result.request_approval(ui)

    # Assert
    assert approved == exp_approved


def test_upload_calls_server_method(mocker, result, comms):
    # Arrange
    spy = mocker.patch.object(comms, "upload_results")
    mocker.patch(PATCH_RESULT.format("Result.todict"), return_value={})
    mocker.patch(PATCH_RESULT.format("Result.set_results"))

    # Act
    result.upload(comms)

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
