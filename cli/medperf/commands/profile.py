import os
import typer
import configparser

from medperf import config
from medperf.utils import parse_context_args, dict_pretty_print, pretty_error

app = typer.Typer()

def read_config():
	config_p = configparser.ConfigParser()
	config_path = os.path.join(config.storage, config.config_path)
	config_p.read(config_path)
	return config_p

def write_config(config_p: configparser.ConfigParser):
	config_path = os.path.join(config.storage, config.config_path)
	with open(config_path, "w") as f:
		config_p.write(f)

@app.command("create", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def create(
	ctx: typer.Context,
	name: str = typer.Option(..., "--name", "-n", help="Profile's name"),
):
	"""Creates a new profile for managing and customizing configuration

	Extra options in the format "--key=value" will be handled as custom configuration
	parameters that will be stored under the new profile
	"""
	args = parse_context_args(ctx.args)
	config_p = read_config()

	filtered_params = {k:v for k, v in args.items() if k in config.customizable_params}
	if name in config_p:
		pretty_error("A profile with the same name already exists", config.ui)

	config_p[name] = filtered_params
	write_config(config_p)

@app.command("set", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def set(ctx: typer.Context):
	"""Assign key-value configuration pairs to the current profile.

	Extra options in the format "--key=value" will be handled as custom configuration
	"""
	profile = config.profile
	args = parse_context_args(ctx.args)
	config_p = read_config()

	filtered_params = {k:v for k, v in args.items() if k in config.customizable_params}
	current_config = config_p[profile]
	current_config.update(filtered_params)
	config_p[profile] = current_config
	write_config(config_p)

@app.command("unset", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def unset(ctx: typer.Context):
	"""Removes a set of custom configuration parameters assigned to the current profile.

	A list of space-separated keys is expected
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
	ui = config.ui
	if profile is None:
		profile = config.profile

	config_p = read_config()
	profile_config = config_p[profile]
	dict_pretty_print(profile_config, ui)