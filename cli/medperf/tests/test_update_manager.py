import json

import pytest

from medperf import update_manager
from medperf.exceptions import EditableInstallUpdateError
from medperf.update_manager import UpdateManager


def test_check_for_updates_warns_when_update_available(mocker, ui):
    # Arrange
    mocker.patch.object(
        UpdateManager,
        "get_update_info",
        return_value={
            "update_available": True,
            "current_version": "0.3.0",
            "latest_version": "0.4.0",
            "update_command": "pip install -U medperf",
        },
    )

    # Act
    UpdateManager().check_for_updates()

    # Assert
    ui.print_warning.assert_called_once_with(
        "MedPerf 0.4.0 is available (you have 0.3.0). "
        "Update with: pip install -U medperf"
    )


def test_check_for_updates_is_silent_when_up_to_date(mocker, ui):
    # Arrange
    mocker.patch.object(
        UpdateManager,
        "get_update_info",
        return_value={"update_available": False, "current_version": "0.3.0"},
    )

    # Act
    UpdateManager().check_for_updates()

    # Assert
    ui.print_warning.assert_not_called()


@pytest.mark.parametrize(
    "direct_url,expected",
    [
        ({"dir_info": {"editable": True}, "url": "file:///repo/cli"}, True),
        ({"dir_info": {}, "url": "file:///repo/cli"}, False),
        ({"url": "https://pypi.org/simple/medperf"}, False),
        (None, False),
    ],
)
def test_is_editable_install(mocker, direct_url, expected):
    # Arrange
    dist = mocker.MagicMock()
    dist.read_text.return_value = json.dumps(direct_url) if direct_url else None
    mocker.patch.object(update_manager.importlib_metadata, "distribution", return_value=dist)

    # Act & Assert
    assert UpdateManager().is_editable_install() == expected


def test_is_editable_install_false_when_package_not_found(mocker):
    # Arrange
    mocker.patch.object(
        update_manager.importlib_metadata,
        "distribution",
        side_effect=update_manager.importlib_metadata.PackageNotFoundError,
    )

    # Act & Assert
    assert UpdateManager().is_editable_install() is False


@pytest.mark.parametrize(
    "editable,expected_command",
    [(True, "git pull"), (False, "pip install -U medperf")],
)
def test_update_info_selects_command_by_install_type(
    mocker, editable, expected_command
):
    # Arrange
    mocker.patch.object(UpdateManager, "is_editable_install", return_value=editable)

    # Act
    info = UpdateManager()._make_update_info("0.3.0", "0.4.0")

    # Assert
    assert info["is_editable_install"] == editable
    assert info["update_command"] == expected_command


def test_validate_update_rejects_editable_install(mocker):
    # Arrange
    mocker.patch.object(UpdateManager, "is_editable_install", return_value=True)

    # Act & Assert
    with pytest.raises(EditableInstallUpdateError):
        UpdateManager().validate_update(latest_version="0.4.0")
