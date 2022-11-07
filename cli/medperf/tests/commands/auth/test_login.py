import os
import stat
import pytest
from unittest.mock import mock_open

import medperf.config as config
from medperf.commands.auth import Login


@pytest.fixture(params=["token123"])
def comms(mocker, request, comms):
    mocker.patch.object(comms, "login")
    mocker.patch("os.remove")
    mocker.patch("os.chmod")
    comms.token = request.param
    return comms


def test_runs_comms_login(mocker, comms, ui):
    # Arrange
    spy = mocker.patch.object(comms, "login")
    mocker.patch("builtins.open", mock_open())

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once()


@pytest.mark.parametrize("profile", ["default", "test", "user"])
def test_assigns_credentials_to_profile(mocker, profile, comms, ui):
    # Arrange
    profile_backup = config.profile
    config.profile = profile
    creds_path = os.path.join(config.storage, config.credentials_path)
    mocker.patch("os.path.exists", return_value=True)
    spy_read = mocker.patch("configparser.ConfigParser.read")
    spy_set = mocker.patch("configparser.ConfigParser.__setitem__")
    mocker.patch("builtins.open", mock_open())

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy_read.assert_called_once_with(creds_path)
    spy_set.assert_called_once_with(profile, {"token": comms.token})

    # Clean
    config.profile = profile_backup


@pytest.mark.parametrize(
    "comms", ["test123", "wey0u392472340", "tokentoken"], indirect=True
)
def test_writes_new_credentials(mocker, comms, ui):
    # Arrange
    creds_path = os.path.join(config.storage, config.credentials_path)
    spy = mocker.patch("builtins.open", mock_open())
    spy_write = mocker.patch("configparser.ConfigParser.write")
    mocker.patch("os.path.exists", return_value=False)

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once_with(creds_path, "w")
    spy_write.assert_called_once()


def test_sets_credentials_permissions_to_read(mocker, comms, ui):
    # Arrange
    creds_path = os.path.join(config.storage, config.credentials_path)
    spy = mocker.patch("os.chmod")
    mocker.patch("builtins.open", mock_open())
    mocker.patch("os.path.exists", return_value=False)

    # Act
    Login.run("usr", "pwd")

    # Assert
    spy.assert_called_once_with(creds_path, stat.S_IREAD)
