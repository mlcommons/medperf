import pytest
from unittest.mock import call
from typer.testing import CliRunner

from medperf.config_management import read_config
from medperf.commands.profile import app

runner = CliRunner()
PATCH_PROFILE = "medperf.commands.profile.{}"


@pytest.mark.parametrize("profile", ["local", "testauth"])
def test_activate_updates_active_profile(mocker, profile):
    # Act
    runner.invoke(app, ["activate", profile])

    # Assert
    config_p = read_config()
    assert config_p.is_profile_active(profile)


@pytest.mark.parametrize("name", ["new_profile", "fets"])
@pytest.mark.parametrize(
    "args",
    [
        (["--platform=docker"], {"platform": "docker"}),
        (
            ["--server", "fets.org", "--no-cleanup"],
            {"server": "fets.org", "cleanup": False},
        ),
        ([], {}),
    ],
)
def test_create_adds_new_profile(mocker, name, args):
    # Arrange
    in_args, out_cfg = args

    # Act
    runner.invoke(app, ["create", "-n", name] + in_args)

    # Assert
    config_p = read_config()
    assert config_p[name] == {**config_p.profiles["default"], **out_cfg}


def test_create_fails_if_name_exists(mocker):
    # Arrange
    name = "local"

    # Act
    res = runner.invoke(app, ["create", "-n", name])

    # Assert
    assert res.exit_code != 0


@pytest.mark.parametrize(
    "args", [(["--platform", "not_docker"], {"platform": "not_docker"})]
)
def test_set_updates_profile_parameters(mocker, args):
    # Arrange
    in_args, out_cfg = args

    # Act
    runner.invoke(app, ["set"] + in_args)

    # Assert
    config_p = read_config()
    assert config_p.active_profile == {**config_p.profiles["default"], **out_cfg}


def test_ls_prints_profile_names(mocker, ui):
    # Arrange
    spy = mocker.patch.object(ui, "print")
    green_spy = mocker.patch.object(ui, "print_highlight")
    config_p = read_config()

    calls = [
        call("  " + profile)
        for profile in config_p
        if not config_p.is_profile_active(profile)
    ]

    # Act
    runner.invoke(app, ["ls"])

    # Assert
    spy.assert_has_calls(calls)
    green_spy.assert_called_once_with("* " + config_p.active_profile_name)


@pytest.mark.parametrize("profile", ["default", "local"])
def test_view_prints_profile_contents(mocker, profile):
    # Arrange
    spy = mocker.patch(PATCH_PROFILE.format("dict_pretty_print"))
    config_p = read_config()
    cfg = config_p[profile]

    # Act
    runner.invoke(app, ["view", profile])

    # Assert
    spy.assert_called_once_with(cfg, skip_none_values=False)
