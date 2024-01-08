import pandas as pd
from textual.app import ComposeResult
from textual.containers import Center
from textual.widgets import (
    Static,
    Button,
    Label,
    ProgressBar,
)

from rano_monitor.constants import REVIEW_FILENAME
from rano_monitor.utils import package_review_cases
from rano_monitor.handlers.reviewed_handler import ReviewedHandler
from rano_monitor.messages.report_updated import ReportUpdated
from rano_monitor.messages.invalid_subject_updated import InvalidSubjectsUpdated

class Summary(Static):
    """Displays a summary of the report"""

    report = pd.DataFrame()
    dset_path = ""
    invalid_subjects = set()

    def compose(self) -> ComposeResult:
        yield Static("Report Status")
        yield Center(id="summary-content")
        with Center():
            yield Button("package cases for review", id="package-btn")

    def set_reviewed_watchdog(self, reviewed_watchdog: ReviewedHandler):
        self.reviewed_watchdog = reviewed_watchdog

    def on_report_updated(self, message: ReportUpdated) -> None:
        report = message.report
        self.dset_path = message.dset_path
        if len(report) > 0:
            report_df = pd.DataFrame(report)
            self.report = report_df
            self.update_summary()

    def on_invalid_subjects_updated(self, message: InvalidSubjectsUpdated) -> None:
        self.invalid_subjects = message.invalid_subjects
        self.update_summary()

    def update_summary(self):
        report_df = self.report
        if report_df.empty:
            return
        package_btn = self.query_one("#package-btn", Button)
        # Generate progress bars for all states
        display_report_df = report_df.copy(deep=True)
        display_report_df.loc[list(self.invalid_subjects), "status_name"] = "INVALIDATED"
        status_percents = display_report_df["status_name"].value_counts() / len(report_df)
        if "DONE" not in status_percents:
            # Attach
            status_percents["DONE"] = 0.0

        package_btn.display = "MANUAL_REVIEW_REQUIRED" in status_percents

        widgets = []
        for name, val in status_percents.items():
            wname = Label(name.capitalize().replace("_", " "))
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
        self.notify(f"{REVIEW_FILENAME} was created on the working directory")

