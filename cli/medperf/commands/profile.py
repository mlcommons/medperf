import os
import typer
import argparse
import configparser

from medperf import config
from medperf.decorators import docstring_parameter
from medperf.utils import dict_pretty_print, pretty_error

def read_config():
    config_p = configparser.ConfigParser()
    config_path = os.path.join(config.storage, config.config_path)
    config_p.read(config_path)
    return config_p


def write_config(config_p: configparser.ConfigParser):
    config_path = os.path.join(config.storage, config.config_path)
    with open(config_path, "w") as f:
        config_p.write(f)


def setup_parser():
    parser = argparse.ArgumentParser(usage="", add_help=False)
    for arg, desc in config.customizable_params.items():
        parser.add_argument(f"--{arg}", help=desc)

    
    return parser


def args_help():
    args_help = [""]
    for arg, desc in config.customizable_params.items():
        arg_help = f"--{arg}: {desc}"
        args_help.append(arg_help)
    
    # Formatting used by typer requires the following join string
    return "\n\n\t".join(args_help)

app = typer.Typer()
parser = setup_parser()


@app.command("create", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@docstring_parameter(args_help())
def create(
    ctx: typer.Context,
    name: str = typer.Option(..., "--name", "-n", help="Profile's name"),
):
    """Creates a new profile for managing and customizing configuration

    Arguments in the format "--key=value" will be handled as custom configuration
    parameters that will be stored under the new profile

    Available arguments:
    {0}
    """
    args = parser.parse_args(ctx.args)
    config_p = read_config()

    if name in config_p:
        pretty_error("A profile with the same name already exists")

    config_p[name] = args
    write_config(config_p)


@app.command("set", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@docstring_parameter(args_help())
def set_args(ctx: typer.Context):
    """Assign key-value configuration pairs to the current profile.

    Arguments in the format "--key=value" will be handled as custom configuration

    Available arguments:
    {0}
    """
    profile = config.profile
    args = parser.parse_args(ctx.args)
    config_p = read_config()

    current_config = config_p[profile]
    current_config.update(args)
    config_p[profile] = current_config
    write_config(config_p)


@app.command("unset", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
@docstring_parameter(args_help())
def unset(ctx: typer.Context):
    """Removes a set of custom configuration parameters assigned to the current profile.

    A list of space-separated keys is expected

    Available arguments:

    {0}
    """
    profile = config.profile
    args = ctx.args
    config_p = read_config()

    for key in args:
        if key in config.customizable_params:
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
