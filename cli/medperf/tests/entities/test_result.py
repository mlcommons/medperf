import pytest
from unittest.mock import MagicMock

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Result

PATCH_RESULT = "medperf.entities.result.{}"


@pytest.fixture
def comms(mocker):
    comms = mocker.create_autospec(spec=Comms)
    return comms


@pytest.fixture
def ui(mocker):
    ui = mocker.create_autospec(spec=UI)
    return ui


@pytest.mark.parametrize(
    "results_path", ["./results.yaml", "~/.medperf/results/1/results.yaml"]
)
def test_todict_opens_results_file_as_yaml(mocker, results_path):
    # Arrange
    open_spy = mocker.patch("builtins.open", MagicMock())
    yaml_spy = mocker.patch("yaml.full_load", return_value={})
    result = Result(results_path, 1, 1, 1)

    # Act
    result.todict()

    # Assert
    open_spy.assert_called_once_with(results_path, "r")
    yaml_spy.assert_called_once()


def test_todict_returns_expected_keys(mocker):
    # Arrange
    mocker.patch("builtins.open", MagicMock())
    mocker.patch("yaml.full_load", return_value={})
    result = Result("", 1, 1, 1)
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


def test_request_approval_skips_if_already_approved(mocker, ui):
    # Arrange
    spy = mocker.patch(PATCH_RESULT.format("approval_prompt"))
    result = Result("", 1, 1, 1)
    result.status = "APPROVED"

    # Act
    result.request_approval(ui)

    # Assert
    spy.assert_not_called()


@pytest.mark.parametrize("exp_approved", [True, False])
def test_request_approval_returns_user_approval(mocker, ui, exp_approved):
    # Arrange
    mocker.patch("typer.echo")
    mocker.patch(PATCH_RESULT.format("dict_pretty_print"))
    mocker.patch(PATCH_RESULT.format("Result.todict"), return_value={})
    mocker.patch(PATCH_RESULT.format("approval_prompt"), return_value=exp_approved)
    result = Result("", 1, 1, 1)

    # Act
    approved = result.request_approval(ui)

    # Assert
    assert approved == exp_approved


def test_upload_calls_server_method(mocker, comms):
    # Arrange
    spy = mocker.patch.object(comms, "upload_results")
    mocker.patch(PATCH_RESULT.format("Result.todict"), return_value={})
    result = Result("", 1, 1, 1)

    # Act
    result.upload(comms)

    # Assert
    spy.assert_called_once()
