import typer
import logging
import logging.handlers
from os.path import abspath, expanduser

from medperf.commands.auth import Login, PasswordChange
from medperf.commands.result import result
import medperf.config as config
from medperf.utils import init_storage, storage_path
from medperf.decorators import clean_except
from medperf.comms import CommsFactory
from medperf.ui import UIFactory
from medperf.commands.mlcube import mlcube
from medperf.commands.dataset import dataset
import medperf.commands.association.association as association


app = typer.Typer()
app.add_typer(mlcube.app, name="mlcube", help="Manage mlcubes")
app.add_typer(result.app, name="result", help="Manage results")
app.add_typer(dataset.app, name="dataset", help="Manage datasets")
app.add_typer(association.app, name="association", help="Manage associations")


@app.command("login")
@clean_except
def login():
    """Login to the medperf server. Must be done only once.
    """
    Login.run(config.comms, config.ui)


@app.command("passwd")
@clean_except
def passwd():
    """Set a new password. Must be logged in.
    """
    comms = config.comms
    ui = config.ui
    comms.authenticate()
    PasswordChange.run(comms, ui)
    ui.print("✅ Done!")


@app.command("run")
@clean_except
def execute(
    benchmark_uid: int = typer.Option(
        ..., "--benchmark", "-b", help="UID of the desired benchmark"
    ),
    data_uid: str = typer.Option(
        ..., "--data_uid", "-d", help="Registered Dataset UID"
    ),
    model_uid: int = typer.Option(
        ..., "--model_uid", "-m", help="UID of model to execute"
    ),
):
    """Runs the benchmark execution step for a given benchmark, prepared dataset and model
    """
    result.run_benchmark(
        benchmark_uid=benchmark_uid, data_uid=data_uid, model_uid=model_uid
    )


@app.callback()
def main(
    log: str = "INFO",
    log_file: str = None,
    comms: str = config.default_comms,
    ui: str = config.default_ui,
    host: str = config.server,
    storage: str = config.storage,
    certificate: str = config.certificate,
    local: bool = typer.Option(
        False, help="Run the CLI with local server configuration"
    ),
):
    # Set configuration variables
    config.storage = abspath(expanduser(storage))
    if log_file is None:
        log_file = storage_path(config.log_file)
    else:
        log_file = abspath(expanduser(log_file))
    if local:
        config.server = config.local_server
        config.certificate = abspath(expanduser(config.local_certificate))
    else:
        config.server = host
        config.certificate = certificate
    config.log_file = log_file

    init_storage()
    log = log.upper()
    log_lvl = getattr(logging, log)
    log_fmt = "%(asctime)s | %(levelname)s: %(message)s"
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10000000, backupCount=5
    )
    handler.setFormatter(logging.Formatter(log_fmt))
    logging.basicConfig(
        level=log_lvl, handlers=[handler], format=log_fmt, datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info(f"Running MedPerf v{config.version} on {log} logging level")

    config.ui = UIFactory.create_ui(ui)
    config.comms = CommsFactory.create_comms(comms, config.ui, config.server)

    config.ui.print(f"MedPerf {config.version}")


if __name__ == "__main__":
    app()
