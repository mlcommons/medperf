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

    config_p["active"]["profile"] = profile
    write_config(config_p)


@app.command("create")
@configurable(with_defaults=True)
def create(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", "-n", help="Profile's name"),
):
    """Creates a new profile for managing and customizing configuration
    """
    args = ctx.config_dict
    config_p = read_config()

    if name in config_p:
        raise InvalidArgumentError("A profile with the same name already exists")

    config_p[name] = args
    write_config(config_p)


@app.command("set")
@configurable()
def set_args(ctx: typer.Context):
    """Assign key-value configuration pairs to the current profile.
    """
    profile = config.profile
    args = ctx.config_dict
    config_p = read_config()

    current_config = config_p[profile]
    current_config.update(args)
    config_p[profile] = current_config
    write_config(config_p)


@app.command("unset")
@configurable(with_args=False)
def unset(ctx: typer.Context):
    """Removes a set of custom configuration parameters assigned to the current profile.
    """
    profile = config.profile
    args = ctx.config_dict
    config_p = read_config()

    for key in args.keys():
        del config_p[profile][key]
    write_config(config_p)


@app.command("ls")
def list():
    """Lists all available profiles
    """
    ui = config.ui
    config_p = read_config()
    for profile in config_p:
        ui.print(profile)


@app.command("view")
def view(profile: str = typer.Argument(None)):
    """Displays a profile's configuration.

    Args:
        profile (str, optional): Profile to display information from. Defaults to active profile.
    """
    if profile is None:
        profile = config.profile

    config_p = read_config()
    profile_config = config_p[profile]
    dict_pretty_print(profile_config)
