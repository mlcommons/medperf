from textual.widgets import ListView, ListItem, Label
import pandas as pd

from rano_monitor.messages.report_updated import ReportUpdated
from rano_monitor.messages.invalid_subject_updated import InvalidSubjectsUpdated

class SubjectListView(ListView):
    report = {}
    highlight = set()
    invalid_subjects = set()

    def on_report_updated(self, message: ReportUpdated) -> None:
        self.report = message.report
        highlight = message.highlight
        self.highlight = self.highlight.union(highlight)
        if len(self.report) > 0:
            self.update_list()

    def on_invalid_subjects_updated(self, message: InvalidSubjectsUpdated) -> None:
        self.invalid_subjects = message.invalid_subjects
        self.update_list()

    def update_list(self):
        # Check for content differences with old report
        # apply alert class to listitem
        report = self.report
        report_df = pd.DataFrame(report)

        subjects = ["SUMMARY"] + list(report_df.index)

        widgets = []
        for subject in subjects:
            if subject == "SUMMARY":
                widget = ListItem(Label(f"{subject}"))
            else:
                status = report_df.loc[subject]["status_name"]
                if subject in self.invalid_subjects:
                    status = "Invalidated"
                widget = ListItem(
                    Label(subject),
                    Label(status.capitalize().replace("_", " "), classes="subtitle")
                )
            if subject in self.highlight:
                widget.set_class(True, "highlight")
            widgets.append(widget)

        current_idx = self.index
        while len(self.children):
            self.children[0].remove()

        self.mount(*widgets)
        self.index = current_idx
