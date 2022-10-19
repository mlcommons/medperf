import pytest
from unittest.mock import call, ANY

from medperf.commands.auth import PasswordChange
from medperf.utils import storage_path
from medperf import config

PATCH_PASSCHANGE = "medperf.commands.auth.password_change.{}"


@pytest.fixture(params=["token123"])
def comms(mocker, request, comms):
    mocker.patch.object(comms, "change_password")
    mocker.patch("os.remove")
    comms.token = request.param
    return comms


def test_run_asks_for_password_twice(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(ui, "hidden_prompt", return_value="pwd")
    calls = [call(ANY), call(ANY)]

    # Act
    PasswordChange.run()

    # Assert
    spy.assert_has_calls(calls)


def test_run_fails_if_password_mismatch(mocker, comms, ui):
    # Arrange
    mocker.patch.object(ui, "hidden_prompt", side_effect=["pwd1", "pwd2"])

    # Act & Assert
    with pytest.raises(SystemExit):
        PasswordChange.run()


def test_run_executes_comms_change_password(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "change_password")

    # Act
    PasswordChange.run()

    # Assert
    spy.assert_called_once()


def test_run_deletes_outdated_token(mocker, comms, ui):
    # Arrange
    cred_path = storage_path(config.credentials_path)
    mocker.patch.object(ui, "hidden_prompt", return_value="pwd")
    spy = mocker.patch("os.remove")

    # Act
    PasswordChange.run()

    # Assert
    spy.assert_called_once_with(cred_path)


def test_run_doesnt_delete_token_if_failed_passchange(mocker, comms, ui):
    # Arrange
    mocker.patch.object(comms, "change_password", return_value=False)
    mocker.patch(PATCH_PASSCHANGE.format("pretty_error"))
    spy = mocker.patch("os.remove")

    # Act
    PasswordChange.run()

    # Assert
    spy.assert_not_called()
