import stat
from medperf.comms import Comms
import medperf.config as config
from medperf.commands import Login
from medperf.utils import storage_path

import pytest
from unittest.mock import mock_open


@pytest.fixture(params=["token123"])
def comms(mocker, request):
    comms = mocker.create_autospec(spec=Comms)
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
    Login.run(comms, ui)

    # Assert
    spy.assert_called_once()


def test_removes_previous_credentials(mocker, comms, ui):
    # Arrange
    creds_path = storage_path(config.credentials_path)
    spy = mocker.patch("os.remove")
    mocker.patch("builtins.open", mock_open())
    mocker.patch("os.path.exists", return_value=True)

    # Act
    Login.run(comms, ui)

    # Assert
    spy.assert_called_once_with(creds_path)


@pytest.mark.parametrize(
    "comms", ["test123", "wey0u392472340", "tokentoken"], indirect=True
)
def test_writes_new_credentials(mocker, comms, ui):
    # Arrange
    m = mock_open()
    creds_path = storage_path(config.credentials_path)
    spy = mocker.patch("builtins.open", m)

    # Act
    Login.run(comms, ui)

    # Assert
    spy.assert_called_once_with(creds_path, "w")
    handle = m()
    handle.write.assert_called_once_with(comms.token)


def test_sets_credentials_permissions_to_read(mocker, comms, ui):
    # Arrange
    creds_path = storage_path(config.credentials_path)
    spy = mocker.patch("os.chmod")
    mocker.patch("builtins.open", mock_open())

    # Act
    Login.run(comms, ui)

    # Assert
    spy.assert_called_once_with(creds_path, stat.S_IREAD)
