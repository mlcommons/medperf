import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import var
from textual.containers import Container, Center, VerticalScroll
from textual.widgets import Header, Rule, Static, Markdown

from rano_monitor.widgets.tarball_subject_view import TarballSubjectView

TITLE = "Tarball RANO Subject Browser"
DESC = "Below you may find the subjects identified within the passed tarball file."

class TarballBrowser(App):
    """Textual tarball browser app."""

    CSS_PATH = "assets/tarball-browser.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    subjects = var([])

    def set_vars(self, tarball_path):
        self.tarball_path = tarball_path
        self.subjects_list = self.__get_subjects()

    def __get_subjects(self):
        subjects = os.listdir(self.tarball_path)
        subject_timepoint_list = []
        for subject in subjects:
            subject_path = os.path.join(self.tarball_path, subject)
            timepoints = os.listdir(subject_path)
            subject_timepoint_list += [(subject, timepoint) for timepoint in timepoints]
        
        return subject_timepoint_list

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(id="main-container"):
            with Container(id="explanation"):
                yield Static(TITLE)
                yield Markdown(DESC)
            with VerticalScroll(id="subjects-container"):
                for id, tp in self.subjects_list:
                    subject_view = TarballSubjectView()
                    subject_view.subject = f"{id}|{tp}"
                    yield subject_view