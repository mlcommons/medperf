import pytest
from copy import deepcopy
from unittest.mock import call
from typer.testing import CliRunner

from medperf import config
from medperf.commands.profile import app

runner = CliRunner()
profile_backup = config.profile
PATCH_PROFILE = "medperf.commands.profile.{}"
MOCKED_CONFIG = {
    "active": {"profile": "default"},
    "default": {},
    "test": {"certificate": "~/.medperf_test.crt", "server": "https://localhost:8000"},
}


@pytest.fixture
def config_p(mocker):
    config_p = deepcopy(MOCKED_CONFIG)
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
    assert config_p["active"]["profile"] == profile
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


@pytest.mark.parametrize("args", [(["--platform", "docker"], {"platform": "docker"})])
def test_set_updates_profile_parameters(mocker, config_p, args):
    # Arrange
    config.profile = "default"
    in_args, out_cfg = args
    write_spy = mocker.patch(PATCH_PROFILE.format("write_config"))
    exp_cfg = deepcopy(config_p[config.profile])
    exp_cfg.update(out_cfg)

    # Act
    runner.invoke(app, ["set"] + in_args)

    # Assert
    assert config_p[config.profile] == exp_cfg
    write_spy.assert_called_once()

    # Clean
    config.profile = profile_backup


@pytest.mark.parametrize(
    "args",
    [
        (["--server"], {"server": True}),
        (["--certificate", "--server"], {"certificate": True, "server": True}),
    ],
)
def test_unset_removes_profile_parameters(config_p, args):
    # Arrange
    config.profile = "default"
    in_args, out_cfg = args

    # Act
    runner.invoke(app, ["unset"] + in_args)

    # Assert
    for param in out_cfg.keys():
        assert param not in config_p[config.profile]

    # Clean
    config.profile = profile_backup


def test_ls_prints_profile_names(mocker, config_p, ui):
    # Arrange
    spy = mocker.patch.object(ui, "print")
    calls = [call(profile) for profile in config_p.keys()]

    # Act
    runner.invoke(app, ["ls"])

    # Assert
    spy.assert_has_calls(calls)


@pytest.mark.parametrize("profile", ["default", "test"])
def test_view_prints_profile_contents(mocker, config_p, profile):
    # Arrange
    spy = mocker.patch(PATCH_PROFILE.format("dict_pretty_print"))
    cfg = config_p[profile]

    # Act
    runner.invoke(app, ["view", profile])

    # Assert
    spy.assert_called_once_with(cfg)
