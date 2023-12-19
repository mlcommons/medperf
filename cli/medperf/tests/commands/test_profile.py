import pytest
from copy import deepcopy
from unittest.mock import call
from typer.testing import CliRunner

from medperf.config_management import ConfigManager
from medperf.utils import default_profile
from medperf.commands.profile import app

runner = CliRunner()
PATCH_PROFILE = "medperf.commands.profile.{}"


@pytest.fixture
def config_p(mocker):
    config_p = ConfigManager()
    config_p.active_profile_name = "default"
    config_p.profiles = {
        "default": default_profile(),
        "test": {
            **default_profile(),
            "certificate": "~/.medperf_test.crt",
            "server": "https://localhost:8000",
        },
    }
    mocker.patch(PATCH_PROFILE.format("read_config"), return_value=config_p)
    mocker.patch(PATCH_PROFILE.format("write_config"))
    return config_p


@pytest.mark.parametrize("profile", ["test", "default"])
def test_activate_updates_active_profile(mocker, config_p, profile):
    # Arrange
    write_spy = mocker.patch(PATCH_PROFILE.format("write_config"))

    # Act
    runner.invoke(app, ["activate", profile])

    # Assert
    assert config_p.is_profile_active(profile)
    write_spy.assert_called_once_with(config_p)


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
def test_create_adds_new_profile(mocker, config_p, name, args):
    # Arrange
    in_args, out_cfg = args
    write_spy = mocker.patch(PATCH_PROFILE.format("write_config"))

    # Act
    runner.invoke(app, ["create", "-n", name] + in_args)

    # Assert
    config_p[name] == out_cfg
    write_spy.assert_called_once_with(config_p)


def test_create_fails_if_name_exists(mocker, config_p):
    # Arrange
    name = "test"
    write_spy = mocker.patch(PATCH_PROFILE.format("write_config"))

    # Act
    runner.invoke(app, ["create", "-n", name])

    # Assert
    write_spy.assert_not_called()


@pytest.mark.parametrize(
    "args", [(["--platform", "not_docker"], {"platform": "not_docker"})]
)
def test_set_updates_profile_parameters(mocker, config_p, args):
    # Arrange
    in_args, out_cfg = args
    write_spy = mocker.patch(PATCH_PROFILE.format("write_config"))
    # conftest is setting config.ui = mocked ui.
    # config_p fixture is calling default_profile.
    # default profile uses config.ui
    # deepcopy-ing mocked ui is causing an error
    # This is a temp fix to figure out what should be done
    config_p.active_profile["ui"] = "CLI"
    config_p.active_profile["comms"] = "REST"
    exp_cfg = deepcopy(config_p.active_profile)
    exp_cfg.update(out_cfg)
    # Act
    runner.invoke(app, ["set"] + in_args)

    # Assert
    assert config_p.active_profile == exp_cfg
    write_spy.assert_called_once()


def test_ls_prints_profile_names(mocker, config_p, ui):
    # Arrange
    spy = mocker.patch.object(ui, "print")
    green_spy = mocker.patch.object(ui, "print_highlight")

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


@pytest.mark.parametrize("profile", ["default", "test"])
def test_view_prints_profile_contents(mocker, config_p, profile):
    # Arrange
    spy = mocker.patch(PATCH_PROFILE.format("dict_pretty_print"))
    cfg = config_p[profile]

    # Act
    runner.invoke(app, ["view", profile])

    # Assert
    spy.assert_called_once_with(cfg, skip_none_values=False)
