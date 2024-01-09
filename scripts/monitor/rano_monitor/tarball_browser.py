import os
import tarfile

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.reactive import var
from textual.containers import Center, VerticalScroll
from textual.widgets import Header, Markdown, Button, Static

from rano_monitor.widgets.tarball_subject_view import TarballSubjectView
from rano_monitor.utils import is_editor_installed
from rano_monitor.constants import REVIEWED_FILENAME

CONTENTS = """
## Tarball RANO Subject Browser

Below you may find the subjects identified within the passed tarball file.
You can review and annotate each case by using the `Review Tumor Segmentation` button.
This button will open ITK SNAP with the provided segmentation file. You can make changes
and save them as necessary. Once you're done with a subject review, press the `Finalize`
button.

In the case where skull stripping was not done correctly you can instead modify the brain
mask by pressing `Review Brain Mask`. This will open the brain mask with ITK SNAP. Once
you're done modifying the brain mask you can save your progress and close the editor.

**NOTE**: Modifying the brain mask invalidates the tumor segmentation for that subject.

Once you're done reviewing all cases, you can package them again into a tarball file by
pressing the `Package cases` button. You can then move this new tarball file to the remote
location where you're running the rano-monitor tool.
"""

class TarballBrowser(App):
    """Textual tarball browser app."""

    CSS_PATH = ["assets/tarball-browser.tcss", "assets/shared.tcss"]
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    subjects = var([])

    def set_vars(self, contents_path):
        self.contents_path = contents_path
        self.subjects_list = self.__get_subjects()

    def __get_subjects(self):
        subjects = os.listdir(self.contents_path)
        subject_timepoint_list = []
        for subject in subjects:
            subject_path = os.path.join(self.contents_path, subject)
            timepoints = os.listdir(subject_path)
            subject_timepoint_list += [(subject, timepoint) for timepoint in timepoints]
        
        return subject_timepoint_list

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="main-container"):
            yield Markdown(CONTENTS)
            with Center():
                yield Button("Package cases", id="package-btn")
            yield Static(
                "ITK-Snap command-line-tools were not found in your system",
                id="review-msg",
                classes="warning",
            )
            with VerticalScroll(id="subjects-container"):
                for id, tp in self.subjects_list:
                    subject_view = TarballSubjectView()
                    subject_view.subject = f"{id}|{tp}"
                    subject_view.contents_path = self.contents_path
                    yield subject_view

    def on_mount(self):
        self.update_subjects_status()

    def update_subjects_status(self):
        subject_views = self.query(TarballSubjectView)
        editor_msg = self.query_one("#review-msg", Static)
        editor_msg.display = "none" if is_editor_installed() else "block"

        for subject_view in subject_views:
            subject_view.update_status()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        package_btn = self.query_one("#package-btn", Button)

        if event.control == package_btn:
            self.package_contents()

    def package_contents(self):
        with tarfile.open(REVIEWED_FILENAME, "w:gz") as tar:
            tar.add(self.contents_path, arcname=os.path.basename(self.contents_path))
        self.notify(f"Cases packaged under {REVIEWED_FILENAME}")