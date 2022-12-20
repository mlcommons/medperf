import typer

from medperf import config
from medperf.decorators import configurable
from medperf.utils import dict_pretty_print, read_config, write_config
from medperf.exceptions import InvalidArgumentError

app = typer.Typer()


@app.command("activate")
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
def create(name: str = typer.Option(..., "--name", "-n", help="Profile's name"),):
    """Creates a new profile for managing and customizing configuration
    """
    config_p = read_config()

    if name in config_p:
        raise InvalidArgumentError("A profile with the same name already exists")

    config_p[name] = {}
    write_config(config_p)


@app.command("set")
@configurable
def set_args(ctx: typer.Context):
    """Assign key-value configuration pairs to the current profile.
    """
    args = ctx.params
    config_p = read_config()

    config_p.active_profile.update(args)
    write_config(config_p)


@app.command("ls")
def list():
    """Lists all available profiles
    """
    ui = config.ui
    config_p = read_config()
    for profile in config_p:
        if config_p.is_profile_active(profile):
            line = f"\033[92m* {profile}\033[0m"
        else:
            line = f"  {profile}"
        ui.print(line)


@app.command("view")
def view(profile: str = typer.Argument(None)):
    """Displays a profile's configuration.

    Args:
        profile (str, optional): Profile to display information from. Defaults to active profile.
    """
    config_p = read_config()
    profile_config = config_p.active_profile
    if profile:
        profile_config = config_p[profile]

    dict_pretty_print(profile_config)


@app.command("delete")
def delete(profile: str):
    """Deletes a profile's configuration.

    Args:
        profile (str): Profile to delete.
    """
    config_p = read_config()
    if profile not in config_p.profiles:
        raise InvalidArgumentError("The provided profile does not exists")

    if profile in [config.default_profile_name, config.test_profile_name]:
        raise InvalidArgumentError("Cannot delete reserved profiles")

    if config_p.is_profile_active(profile):
        raise InvalidArgumentError("Cannot delete a currently activated profile")

    del config_p[profile]
    write_config(config_p)
