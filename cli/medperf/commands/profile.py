import typer
import os
from medperf import config
from medperf.decorators import configurable, clean_except
from medperf.utils import dict_pretty_print
from medperf.config_management import read_config, write_config
from medperf.exceptions import InvalidArgumentError

app = typer.Typer()


@app.command("activate")
@clean_except
def activate(profile: str):
    """Assigns the active profile, which is used by default

    Args:
        profile (str): Name of the profile to be used.
    """
    config_p = read_config()

    if profile not in config_p:
        raise InvalidArgumentError("The provided profile does not exists")

    config_p.activate(profile)
    write_config(config_p)


@app.command("create")
@clean_except
@configurable
def create(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", "-n", help="Profile's name"),
):
    """Creates a new profile for managing and customizing configuration"""
    args = ctx.params
    args.pop("name")
    config_p = read_config()

    if name in config_p:
        raise InvalidArgumentError("A profile with the same name already exists")

    config_p[name] = args
    write_config(config_p)


@app.command("set")
@clean_except
@configurable
def set_args(ctx: typer.Context):
    """Assign key-value configuration pairs to the current profile."""
    args = ctx.params
    config_p = read_config()

    config_p.active_profile.update(args)
    write_config(config_p)


@app.command("ls")
@clean_except
def list():
    """Lists all available profiles"""
    ui = config.ui
    config_p = read_config()
    for profile in config_p:
        if config_p.is_profile_active(profile):
            ui.print_highlight("* " + profile)
        else:
            ui.print("  " + profile)


@app.command("view")
@clean_except
def view(profile: str = typer.Argument(None)):
    """Displays a profile's configuration.

    Args:
        profile (str, optional): Profile to display information from. Defaults to active profile.
    """
    config_p = read_config()
    profile_config = config_p.active_profile
    if profile:
        profile_config = config_p[profile]

    profile_config.pop(config.credentials_keyword, None)
    profile_name = profile if profile else config_p.active_profile_name
    # for consistency with env variable:
    profile_name = os.environ.get("MEDPERF_ACTIVE_PROFILE", profile_name)

    config.ui.print(f"\nProfile '{profile_name}':")
    dict_pretty_print(profile_config, skip_none_values=False)


@app.command("delete")
@clean_except
def delete(profile: str):
    """Deletes a profile's configuration.

    Args:
        profile (str): Profile to delete.
    """
    config_p = read_config()
    if profile not in config_p.profiles:
        raise InvalidArgumentError("The provided profile does not exists")

    if profile in [
        config.default_profile_name,
        config.testauth_profile_name,
        config.test_profile_name,
    ]:
        raise InvalidArgumentError("Cannot delete reserved profiles")

    if config_p.is_profile_active(profile):
        raise InvalidArgumentError("Cannot delete a currently activated profile")

    del config_p[profile]
    write_config(config_p)
