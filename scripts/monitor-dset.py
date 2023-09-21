"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import os
from pathlib import Path
import typer
from tabulate import tabulate
from typer import Argument
from medperf.utils import storage_path, read_config, set_custom_config
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from medperf import config
import yaml
import pandas as pd

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Center
from textual.reactive import var, reactive
from textual.message import Message
from textual.widgets import (
    ListView,
    ListItem,
    Label,
    Footer,
    Header,
    Static,
    Button,
    ProgressBar,
)
from textual.worker import Worker, get_current_worker

NAME_HELP = "The name of the dataset to monitor"
MLCUBE_HELP = "The Data Preparation MLCube UID used to create the data"
LISTITEM_MAX_LEN = 30


def to_local_path(mlcube_path: str, local_parent_path: str):
    mlcube_prefix = "/mlcube_io"
    if len(mlcube_path) == 0:
        return ""

    if not mlcube_path.startswith(mlcube_prefix):
        raise RuntimeError(
            f"{mlcube_path} doesn't start with expected prefix: {mlcube_prefix}"
        )

    # normalize both paths
    path = Path(*Path(mlcube_path).parts[2:])
    parent_path = str(Path(local_parent_path))
    return os.path.join(parent_path, str(path))


class ReportState:
    def __init__(self, report_path: str, app):
        self.report_path = report_path
        self.app = app
        self.report = None

    def update(self):
        with open(self.report_path, "r") as f:
            report_dict = yaml.safe_load(f)
        self.report = report_dict
        self.__update_app()

    def __update_app(self):
        self.app.report = self.report


class ReportHandler(FileSystemEventHandler):
    def __init__(self, report_state: ReportState):
        self.report_state = report_state

    def on_modified(self, event):
        if event.src_path == self.report_state.report_path:
            self.report_state.update()


class PromptHandler(FileSystemEventHandler):
    def __init__(self, dset_data_path: str, textual_app):
        self.dset_data_path = dset_data_path
        self.prompt_path = os.path.join(dset_data_path, ".prompt.txt")
        self.app = textual_app
        if os.path.exists(self.prompt_path):
            self.display_prompt()

    def on_created(self, event):
        if event.src_path == self.prompt_path:
            self.display_prompt()

    def on_modified(self, event):
        self.on_created(event)

    def display_prompt(self):
        with open(self.prompt_path, "r") as f:
            prompt = f.read()
        self.app.update_prompt(prompt)
        # _confirm_dset(self.manager, prompt, self.dset_data_path)


class ReportUpdated(Message):
    def __init__(self, report: dict):
        self.report = report
        super().__init__()


class Summary(Static):
    """Displays a summary of the report"""

    def compose(self) -> ComposeResult:
        yield Static("Report Status")
        yield Center(id="summary-content")

    def on_report_updated(self, message: ReportUpdated) -> None:
        report = message.report
        if len(report) > 0:
            self.update_summary(message.report)

    def update_summary(self, report: dict):
        report_df = pd.DataFrame(report)
        # Generate progress bars for all states
        status_percents = report_df["status_name"].value_counts() / len(report_df)
        if "DONE" not in status_percents:
            # Attach
            status_percents["DONE"] = 0.0

        widgets = []
        for name, val in status_percents.items():
            wname = Label(name)
            wpbar = ProgressBar(total=1, show_eta=False)
            wpbar.advance(val)
            widget = Center(wname, wpbar, classes="pbar")
            widgets.append(widget)

        # Cleanup the current state of progress bars
        content = self.query_one("#summary-content")
        while len(content.children):
            content.children[0].remove()

        content.mount(*widgets)


class SubjectListView(ListView):
    report = {}

    def on_report_updated(self, message: ReportUpdated) -> None:
        report = message.report
        if len(report) > 0:
            self.update_list(message.report)

    def update_list(self, report: dict):
        # Check for content differences with old report
        # apply alert class to listitem
        report_df = pd.DataFrame(report)

        subjects = ["SUMMARY"] + list(report_df.index)
        ellipsis_subjects = []
        for subject in subjects:
            if len(subject) > LISTITEM_MAX_LEN:
                idx = LISTITEM_MAX_LEN - 3
                subject = subject[:idx] + "..."

            ellipsis_subjects.append(subject)

        widgets = []
        for subject in ellipsis_subjects:
            widgets.append(ListItem(Label(subject)))

        current_idx = self.index
        while len(self.children):
            self.children[0].remove()

        self.mount(*widgets)
        self.index = current_idx
        self.report = report


class SubjectDetails(Static):
    def compose(self) -> ComposeResult:
        with Center(id="subject-title"):
            yield Static(id="subject-name")
            yield Static(id="subject-status")
        with Horizontal(id="subject-comment-container"):
            yield Static("Comment: ", classes="subject-item-label")
            yield Static(id="subject-comments", classes="subject-item-content")
        with Horizontal(id="subject-data-container"):
            yield Static("Data path: ", classes="subject-item-label")
            yield Static(id="subject-data-path", classes="subject-item-content")
        with Horizontal(id="subject-labels-container"):
            yield Static("Labels path: ", classes="subject-item-label")
            yield Static(id="subject-labels-path", classes="subject-item-content")

    def update_subject(self, subject: pd.Series, dset_path: str):
        wname = self.query_one("#subject-name", Static)
        wstatus = self.query_one("#subject-status", Static)
        wmsg = self.query_one("#subject-comments", Static)
        wdata = self.query_one("#subject-data-path", Static)
        wlabels = self.query_one("#subject-labels-path", Static)

        labels_path = os.path.join(dset_path, "../labels")
        wname.update(subject.name)
        wstatus.update(subject["status_name"])
        wmsg.update(subject["comment"])
        wdata.update(to_local_path(subject["data_path"], dset_path))
        wlabels.update(to_local_path(subject["labels_path"], labels_path))

        # Only display labels if there's content
        labels_container = self.query_one("#subject-labels-container", Horizontal)
        labels_container.display = len(subject["labels_path"]) > 0


class Subjectbrowser(App):
    """Textual subject browser app."""

    CSS_PATH = "assets/monitor-dset.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("y", "respond('y')", "Yes", show=False),
        Binding("n", "respond('n')", "No", show=False),
    ]

    subjects = var([])
    report = reactive({})
    pbars = var([])
    prompt = ""

    def set_dset_data_path(self, dset_data_path: str):
        self.dset_data_path = dset_data_path

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        with Container():
            with Container(id="list-container"):
                yield SubjectListView(id="subjects-list")
            yield Summary(id="summary")
            yield SubjectDetails(id="details")
        with Container(id="confirm-prompt"):
            yield Static(self.prompt, id="confirm-details")
            yield Horizontal(
                Button("[Y] Yes", id="confirm-approve", variant="success"),
                Button("[N] No", id="confirm-deny", variant="error"),
                id="confirm-buttons",
            )
        yield Footer()

    def on_mount(self):
        # Hide the confirm prompt
        container = self.query_one("#confirm-prompt", Container)
        container.display = False

        # Load report for the first time
        report_path = os.path.join(self.dset_data_path, "..", "report.yaml")
        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                self.report = yaml.safe_load(f)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Called when the user click a subject in the list."""
        # TODO: Construct a renderable of the subject details
        subject_idx = event.item.children[0].renderable.plain
        summary_container = self.query_one("#summary", Summary)
        subject_container = self.query_one("#details", Static)
        if subject_idx == "SUMMARY":
            # Render the summary
            summary_container.display = True
            subject_container.display = False
            return
        else:
            summary_container.display = False
            subject_container.display = True

        report = pd.DataFrame(self.report)
        subject = report.loc[subject_idx]
        subject_view = self.query_one("#details", SubjectDetails)
        subject_view.update_subject(subject, self.dset_data_path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        y_button = self.query_one("#confirm-approve", Button)
        n_button = self.query_one("#confirm-deny", Button)

        if event.control == y_button:
            self.action_respond("y")
        elif event.control == n_button:
            self.action_respond("n")

    def update_prompt(self, prompt: str):
        self.prompt = prompt
        show_prompt = bool(len(prompt))
        try:
            prompt_details = self.query_one("#confirm-details", Static)
            prompt_details.update(prompt)
            container = self.query_one("#confirm-prompt", Container)
            container.display = show_prompt
        except:
            return

    def watch_report(self, report: dict) -> None:
        # self.update_summary(report)
        # TODO: compare with old report
        # Get rows that changed and highlight them on the list
        # if the currently viewed row changed, update the details
        self.notify("report changed")
        msg = ReportUpdated(report)
        summary = self.query_one("#summary", Summary)
        subjectlist = self.query_one("#subjects-list", SubjectListView)

        summary.post_message(msg)
        subjectlist.post_message(msg)
        # report_df = pd.DataFrame(report)

    def action_respond(self, answer: str):
        if len(self.prompt) == 0:
            # Only act when there's a prompt
            return
        response_path = os.path.join(self.dset_data_path, ".response.txt")
        with open(response_path, "w") as f:
            f.write(answer)

        try:
            container = self.query_one("#confirm-prompt", Container)
            container.display = False
        except:
            return


def main(
    name: str = Argument(..., help=NAME_HELP),
    mlcube_uid: int = Argument(..., help=MLCUBE_HELP),
):
    config_p = read_config()
    set_custom_config(config_p.active_profile)

    staging_path = storage_path(config.staging_data_storage)
    dset_path = os.path.join(staging_path, f"{name}_{mlcube_uid}")

    if not os.path.exists(dset_path):
        print(
            "The provided dataset could not be found. Please ensure the name and ID are correct"
        )
        print()
        print("AVAILABLE DATASETS")
        display_available_dsets()

    report_path = os.path.join(dset_path, "report.yaml")
    dset_data_path = os.path.join(dset_path, "data")

    if not os.path.exists(report_path):
        print(
            "The report file was not found. This probably means it has not yet been created."
        )
        print("Please wait a while before running this tool again")
        exit()

    app = Subjectbrowser()
    app.set_dset_data_path(dset_data_path)

    report_state = ReportState(report_path, app)
    # report_state.update()
    observer = Observer()
    observer.schedule(ReportHandler(report_state), dset_path)
    observer.schedule(
        PromptHandler(dset_data_path, app), os.path.join(dset_path, "data")
    )
    observer.start()
    app.run()

    observer.stop()


def display_available_dsets():
    staging_path = storage_path(config.staging_data_storage)
    available_staging_dsets = os.listdir(staging_path)
    staging_dsets_params = [dset.split("_") for dset in available_staging_dsets]
    headers = ["Dataset Name", "MLCube ID"]
    print(tabulate(staging_dsets_params, headers=headers))


if __name__ == "__main__":
    typer.run(main)
