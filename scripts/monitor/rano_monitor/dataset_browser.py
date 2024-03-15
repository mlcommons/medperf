import os
import webbrowser

import pandas as pd
import yaml
from rano_monitor.messages import InvalidSubjectsUpdated
from rano_monitor.messages import ReportUpdated
from rano_monitor.utils import generate_full_report
from rano_monitor.widgets.subject_details import SubjectDetails
from rano_monitor.widgets.subject_list_view import SubjectListView
from rano_monitor.widgets.summary import Summary
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive, var
from textual.widgets import (
    Button,
    Footer,
    Header,
    ListView,
    Static,
)


class DatasetBrowser(App):
    """Textual dataset browser app."""

    CSS_PATH = ["assets/subject-browser.tcss", "assets/shared.tcss"]
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("y", "respond('y')", "Yes", show=False),
        Binding("n", "respond('n')", "No", show=False),
    ]

    subjects = var([])
    report = reactive({})
    pbars = var([])
    invalid_subjects = reactive(set())
    prompt = ""

    def set_vars(
        self,
        dset_data_path,
        stages_path,
        reviewed_watchdog,
        output_path,
        invalid_path,
        invalid_watchdog,
        prompt_watchdog,
    ):
        self.dset_data_path = dset_data_path
        self.stages_path = stages_path
        self.reviewed_watchdog = reviewed_watchdog
        self.output_path = output_path
        self.invalid_path = invalid_path
        self.invalid_watchdog = invalid_watchdog
        self.prompt_watchdog = prompt_watchdog

    def update_invalid(self, invalid_subjects):
        self.invalid_subjects = invalid_subjects

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
                    "[N] No",
                    id="confirm-deny",
                    variant="error",
                    classes="prompt-btn",
                ),
                id="confirm-buttons",
            )
        yield Footer()

    def on_mount(self):
        # Hide the confirm prompt
        container = self.query_one("#confirm-prompt", Container)
        container.display = False

        # Set title - subtitle
        self.title = "Subject Browser"
        self.sub_title = os.getcwd()

        # Load report for the first time
        report_path = os.path.join(self.dset_data_path, "..", "report.yaml")
        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                self.report = yaml.safe_load(f)

        # Set invalid path for subject view
        subject_details = self.query_one("#details", SubjectDetails)
        subject_details.set_invalid_path(self.invalid_path)

        # Execute handlers
        self.prompt_watchdog.manual_execute()
        self.invalid_watchdog.manual_execute()

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
        subject_view.subject = subject
        subject_view.dset_path = self.dset_data_path

        subject_view.update_subject()

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
        prompt_details = self.query_one("#confirm-details", Static)
        prompt_details.update(prompt)
        container = self.query_one("#confirm-prompt", Container)
        container.display = show_prompt
        container.focus()

    def watch_invalid_subjects(self, invalid_subjects: set) -> None:
        subject_list = self.query_one("#subjects-list", SubjectListView)
        summary = self.query_one("#summary", Summary)
        subject_details = self.query_one("#details", SubjectDetails)

        msg = InvalidSubjectsUpdated(invalid_subjects)
        subject_list.post_message(msg)
        summary.post_message(msg)
        subject_details.post_message(msg)

    def watch_report(self, old_report: dict, report: dict) -> None:
        highlight_subjects = set()

        report = generate_full_report(report, self.stages_path)

        # There was an old report, check the differences
        report_df = pd.DataFrame(report)
        old_report_df = pd.DataFrame(old_report)

        try:
            # Make both dataset identically labeled
            if len(report_df) > len(old_report_df):
                old_report_df = old_report_df.reindex(index=report_df.index)
            elif len(old_report_df) > len(report_df):
                report_df = report_df.reindex(index=old_report_df.index)

            diff = report_df.compare(old_report_df)
            highlight_subjects = set(diff.index)
            self.notify("report changed")
        except ValueError:
            # Could not make the comparison, update freely
            pass

        msg = ReportUpdated(report, highlight_subjects, self.dset_data_path)
        summary = self.query_one("#summary", Summary)
        subjectlist = self.query_one("#subjects-list", SubjectListView)

        summary.post_message(msg)
        subjectlist.post_message(msg)

        # Write the report into a csv
        if self.output_path is not None:
            report_df.to_csv(self.output_path, index=None)

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
        except Exception:
            return

    def action_open_url(self, url):
        webbrowser.open(url, new=0, autoraise=True)
