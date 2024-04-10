import os
import tarfile

import typer
from rano_monitor.constants import (
    DSET_HELP,
    DEFAULT_STAGES_PATH,
    STAGES_HELP,
    DSET_LOC_HELP,
    OUT_HELP
)
from rano_monitor.dataset_browser import DatasetBrowser
from rano_monitor.handlers import InvalidHandler
from rano_monitor.handlers import PromptHandler
from rano_monitor.handlers import ReportHandler, ReportState
from rano_monitor.handlers import TarballReviewedHandler
from rano_monitor.tarball_browser import TarballBrowser
from typer import Option, Argument
from watchdog.observers import Observer

app = typer.Typer()


def run_dset_app(dset_path, stages_path, output_path):
    report_path = os.path.join(dset_path, "report.yaml")
    dset_data_path = os.path.join(dset_path, "data")
    invalid_path = os.path.join(dset_path, "metadata/.invalid.txt")

    if not os.path.exists(report_path):
        print(
            "The report file was not found. "
            "This probably means it has not yet been created."
        )
        print("Please wait a while before running this tool again")
        exit()

    t_app = DatasetBrowser()

    report_state = ReportState(report_path, t_app)
    report_watchdog = ReportHandler(report_state)
    prompt_watchdog = PromptHandler(dset_data_path, t_app)
    invalid_watchdog = InvalidHandler(invalid_path, t_app)

    t_app.set_vars(
        dset_data_path,
        stages_path,
        output_path,
        invalid_path,
        invalid_watchdog,
        prompt_watchdog,
    )

    observer = Observer()
    observer.schedule(report_watchdog, dset_path)
    observer.schedule(prompt_watchdog, os.path.join(dset_path, "data"))
    observer.schedule(invalid_watchdog, os.path.dirname(invalid_path))
    observer.start()
    t_app.run()

    observer.stop()


def run_tarball_app(tarball_path):
    folder_name = f".{os.path.basename(tarball_path).split('.')[0]}"
    contents_path = os.path.join(os.path.dirname(tarball_path), folder_name)
    if not os.path.exists(contents_path):
        with tarfile.open(tarball_path) as tar:
            tar.extractall(path=contents_path)

    t_app = TarballBrowser()

    contents_path = os.path.join(contents_path, "review_cases")
    reviewed_watchdog = TarballReviewedHandler(contents_path, t_app)

    t_app.set_vars(contents_path)

    observer = Observer()
    observer.schedule(reviewed_watchdog, path=contents_path, recursive=True)
    observer.start()

    t_app.run()

    observer.stop()


@app.command()
def main(
    dataset_uid: str = Option(..., "-d", "--dataset", help=DSET_HELP),
    stages_path: str = Option(
        DEFAULT_STAGES_PATH,
        "-s",
        "--stages",
        help=STAGES_HELP
    ),
    dset_path: str = Option(
        None,
        "-p",
        "--path",
        help=DSET_LOC_HELP,
    ),
    output_path: str = Option(None, "-o", "--out", help=OUT_HELP),
):
    if dataset_uid.endswith(".tar.gz"):
        # TODO: implement tarball_app
        run_tarball_app(dataset_uid)
        return
    elif dataset_uid.isdigit():
        # Only import medperf dependencies if the user intends to use medperf
        from medperf import config
        from medperf.init import initialize

        initialize()
        dset_path = os.path.join(config.datasets_folder, dataset_uid)
    else:
        dset_path = dataset_uid

    if not os.path.exists(dset_path):
        print(
            "The provided dataset could not be found. "
            "Please ensure the passed dataset UID/path is correct"
        )

    run_dset_app(dset_path, stages_path, output_path)


if __name__ == "__main__":
    typer.run(main)
