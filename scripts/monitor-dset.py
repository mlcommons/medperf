"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import os
from pathlib import Path
import typer
import pyperclip
from tabulate import tabulate
from typer import Argument
from medperf.utils import storage_path, read_config, set_custom_config
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from medperf import config
import yaml
import pandas as pd
import tarfile

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
    mlcube_prefix = "mlcube_io"
    if len(mlcube_path) == 0:
        return ""

    if mlcube_path.startswith(os.path.sep):
        mlcube_path = mlcube_path[1:]

    if mlcube_path.startswith(mlcube_prefix):
        # normalize path
        mlcube_path = str(Path(*Path(mlcube_path).parts[2:]))

    local_parent_path = str(Path(local_parent_path))
    return os.path.normpath(os.path.join(local_parent_path, mlcube_path))


def package_review_cases(report: pd.DataFrame, dset_path: str):
    review_cases = report[report["status_name"] == "MANUAL_REVIEW_REQUIRED"]
    with tarfile.open("review_cases.tar.gz", "w:gz") as tar:
        for i, row in review_cases.iterrows():
            labels_path = to_local_path(row["labels_path"], dset_path)

            id, tp = row.name.split("|")
            tar_path = os.path.join("review_cases", id, tp)
            reviewed_path = os.path.join("review_cases", id, tp, "reviewed")
            reviewed_dir = tarfile.TarInfo(name=reviewed_path)
            reviewed_dir.type = tarfile.DIRTYPE
            reviewed_dir.mode = 0o755
            tar.addfile(reviewed_dir)
            tar.add(labels_path, tar_path)


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
    def __init__(self, report: dict, highlight: set, dset_path: str):
        self.report = report
        self.highlight = highlight
        self.dset_path = dset_path
        super().__init__()


class Summary(Static):
    """Displays a summary of the report"""

    report = None
    dset_path = ""

    def compose(self) -> ComposeResult:
        yield Static("Report Status")
        yield Center(id="summary-content")
        with Center():
            yield Button("packages cases for review", id="package-btn")

    def on_report_updated(self, message: ReportUpdated) -> None:
        report = message.report
        self.dset_path = message.dset_path
        if len(report) > 0:
            self.update_summary(message.report)

    def update_summary(self, report: dict):
        report_df = pd.DataFrame(report)
        self.report = report_df
        package_btn = self.query_one("#package-btn", Button)
        # Generate progress bars for all states
        status_percents = report_df["status_name"].value_counts() / len(report_df)
        if "DONE" not in status_percents:
            # Attach
            status_percents["DONE"] = 0.0

        package_btn.display = "MANUAL_REVIEW_REQUIRED" in status_percents

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        package_review_cases(self.report, self.dset_path)
        self.notify("review_cases.tar.gz was created on the working directory")


class SubjectListView(ListView):
    report = {}
    highlight = set()

    def on_report_updated(self, message: ReportUpdated) -> None:
        report = message.report
        highlight = message.highlight
        self.highlight = self.highlight.union(highlight)
        if len(report) > 0:
            self.update_list(report)

    def update_list(self, report: dict):
        # Check for content differences with old report
        # apply alert class to listitem
        report_df = pd.DataFrame(report)

        subjects = ["SUMMARY"] + list(report_df.index)

        widgets = []
        for subject in subjects:
            widget = ListItem(Label(subject))
            if subject in self.highlight:
                widget.set_class(True, "highlight")
            widgets.append(widget)

        current_idx = self.index
        while len(self.children):
            self.children[0].remove()

        self.mount(*widgets)
        self.index = current_idx
        self.report = report


class CopyableItem(Static):
    content = reactive("")

    def __init__(self, label: str, content: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = label
        self.content = content

    def compose(self) -> ComposeResult:
        yield Static(f"{self.label}: ", classes="subject-item-label")
        yield Static(self.content, classes="subject-item-content")
        yield Button("⎘", classes="subject-item-copy")

    def update(self, content):
        self.content = content

    def watch_content(self, content):
        if len(content) == 0:
            self.display = False
            return
        subject = self.query_one(".subject-item-content", Static)
        subject.update(content)
        self.display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        pyperclip.copy(self.content)
        self.notify("Text copied to clipboard")


class SubjectDetails(Static):
    def compose(self) -> ComposeResult:
        with Center(id="subject-title"):
            yield Static(id="subject-name")
            yield Static(id="subject-status")
        yield CopyableItem("Comment", "", id="subject-comment-container")
        yield CopyableItem("Data path", "", id="subject-data-container")
        yield CopyableItem("Labels path", "", id="subject-labels-container")

    def update_subject(self, subject: pd.Series, dset_path: str):
        wname = self.query_one("#subject-name", Static)
        wstatus = self.query_one("#subject-status", Static)
        wmsg = self.query_one("#subject-comment-container", CopyableItem)
        wdata = self.query_one("#subject-data-container", CopyableItem)
        wlabels = self.query_one("#subject-labels-container", CopyableItem)

        labels_path = os.path.join(dset_path, "../labels")
        wname.update(subject.name)
        wstatus.update(subject["status_name"])
        wmsg.update(subject["comment"])
        wdata.update(to_local_path(subject["data_path"], dset_path))
        wlabels.update(to_local_path(subject["labels_path"], labels_path))


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
                Button(
                    "[Y] Yes",
                    id="confirm-approve",
                    variant="success",
                    classes="prompt-btn",
                ),
                Button(
                    "[N] No", id="confirm-deny", variant="error", classes="prompt-btn"
                ),
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
        subject_idx = event.item.children[0].renderable.plain
        listview = self.query_one("#subjects-list", SubjectListView)
        event.item.set_class(False, "highlight")
        if subject_idx in listview.highlight:
            listview.highlight.remove(subject_idx)
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
            container.focus()
        except:
            return

    def watch_report(self, old_report: dict, report: dict) -> None:
        # self.update_summary(report)
        # TODO: compare with old report
        # Get rows that changed and highlight them on the list
        # if the currently viewed row changed, update the details
        highlight_subjects = set()
        if len(old_report) == len(report):
            # There was an old report, check the differences
            report_df = pd.DataFrame(report)
            old_report_df = pd.DataFrame(old_report)
            diff = report_df.compare(old_report_df)
            highlight_subjects = set(diff.index)

        self.notify("report changed")
        msg = ReportUpdated(report, highlight_subjects, self.dset_data_path)
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
