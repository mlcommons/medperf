import os
import pandas as pd
from rano_monitor.constants import REVIEW_FILENAME, REVIEWED_FILENAME, MANUAL_REVIEW_STAGE, DONE_STAGE
from rano_monitor.messages import InvalidSubjectsUpdated
from rano_monitor.messages import ReportUpdated
from rano_monitor.messages import AnnotationsLoaded
from rano_monitor.utils import package_review_cases, unpackage_reviews
from textual.app import ComposeResult
from textual.containers import Center
from textual.widgets import (
    Button,
    Label,
    ProgressBar,
    Static,
)


class Summary(Static):
    """Displays a summary of the report"""

    report = pd.DataFrame()
    dset_path = ""
    invalid_subjects = set()

    def compose(self) -> ComposeResult:
        yield Static("Report Status")
        yield Static(
            "HINT: To move forward with processing and finalized annotations, ensure the preparation pipeline is running.",
            id="hint-msg",
            classes="warning",
        )
        yield Center(id="summary-content")
        with Center(id="package-btns"):
            yield Button(
                "package cases for review", classes="review-btn", id="package-btn"
            )
            yield Button(
                "Load reviewed_cases.tar.gz", classes="review-btn", id="unpackage-btn"
            )

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
        package_btns = self.query_one("#package-btns", Center)
        # Generate progress bars for all states
        display_report_df = report_df.copy(deep=True)
        display_report_df.loc[list(self.invalid_subjects), "status_name"] = (
            "INVALIDATED"
        )
        status_counts = display_report_df["status_name"].value_counts()
        status_percents = status_counts / len(report_df)
        if "DONE" not in status_percents:
            # Attach
            status_percents["DONE"] = 0.0

        abs_status = display_report_df["status"].abs()
        is_beyond_manual_review = (abs_status >= MANUAL_REVIEW_STAGE)
        is_not_done = (abs_status < DONE_STAGE)
        package_btns.display = any(is_beyond_manual_review & is_not_done)

        widgets = []
        for name, val in status_percents.items():
            count = status_counts[name] if name in status_counts else 0
            wname = Label(
                f'{name.capitalize().replace("_", " ")} ({count}/{len(report_df)})'
            )
            wpbar = ProgressBar(total=1, show_eta=False)
            wpbar.advance(val)
            widget = Center(wname, wpbar, classes="pbar")
            widgets.append(widget)

        # Cleanup the current state of progress bars
        content = self.query_one("#summary-content")
        while len(content.children):
            content.children[0].remove()

        content.mount(*widgets)

    async def _package_review_cases(self):
        pkg_btn = self.query_one("#package-btn", Button)
        label = pkg_btn.label
        pkg_btn.disabled = True
        pkg_btn.label = "Creating package..."
        self.notify("Packaging review cases. This may take a while")
        package_review_cases(self.report, self.dset_path)
        self.notify(f"{REVIEW_FILENAME} was created on the working directory")
        pkg_btn.label = label
        pkg_btn.disabled = False

    async def _unpackage_reviews(self):
        unpkg_btn = self.query_one("#unpackage-btn", Button)
        label = unpkg_btn.label
        unpkg_btn.disabled = True
        unpkg_btn.label = "Loading annotations..."
        self.notify("Loading annotations. This may take a while")
        unpackage_reviews(REVIEWED_FILENAME, self, self.dset_path)
        self.notify("Annotations have been loaded")
        unpkg_btn.label = label
        unpkg_btn.disabled = False
        self.post_message(AnnotationsLoaded())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        pkg_btn = self.query_one("#package-btn", Button)
        unpkg_btn = self.query_one("#unpackage-btn", Button)

        if event.control == pkg_btn:
            self.run_worker(self._package_review_cases(), exclusive=True, thread=True)
        elif event.control == unpkg_btn:
            if REVIEWED_FILENAME not in os.listdir("."):
                self.notify(f"{REVIEWED_FILENAME} not found in {os.path.abspath('.')}")
                return

            self.run_worker(self._unpackage_reviews(), exclusive=True, thread=True)
