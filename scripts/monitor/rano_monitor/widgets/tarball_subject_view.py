import os

from rano_monitor.constants import BRAINMASK, BRAINMASK_BAK, DEFAULT_SEGMENTATION
from rano_monitor.utils import (
    finalize,
    get_hash,
    is_editor_installed,
    review_brain,
    review_tumor,
)
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Static


class TarballSubjectView(Static):
    subject = reactive("")
    contents_path = reactive("")
    review_cmd = None  # This will be assigned after initialized

    def compose(self) -> ComposeResult:
        with Horizontal(classes="subject-item"):
            with Container(classes="subject-text"):
                yield Static(self.subject)
                yield Static("Brain mask modified", classes="brain-status")
                yield Static("Tumor segmentation reviewed", classes="tumor-status")

            yield Button("Review Brain Mask", classes="brain-btn")
            yield Button("Review Tumor Segmentation", classes="tumor-btn")
            yield Button.success("Finalize", classes="finalize-btn")

    def on_mount(self):
        tumor_btn = self.query_one(".tumor-btn", Button)
        finalize_btn = self.query_one(".finalize-btn", Button)
        brain_btn = self.query_one(".brain-btn", Button)
        tumor_status = self.query_one(".tumor-status", Static)
        brain_status = self.query_one(".brain-status", Static)

        finalize_btn.disabled = True
        brain_btn.disabled = True
        tumor_btn.disabled = True
        tumor_status.display = "none"
        brain_status.display = "none"

        self.__update_buttons()
        self.update_status()

    def update_status(self):
        tumor_status = self.query_one(".tumor-status", Static)
        brain_status = self.query_one(".brain-status", Static)
        if self.__tumor_has_been_finalized():
            tumor_status.display = "block"
        if self.__brain_has_been_reviewed():
            brain_status.display = "block"

    def __update_buttons(self):
        tumor_btn = self.query_one(".tumor-btn", Button)
        finalize_btn = self.query_one(".finalize-btn", Button)
        brain_btn = self.query_one(".brain-btn", Button)
        if is_editor_installed(self.review_cmd):
            tumor_btn.disabled = False
        if self.__can_finalize():
            finalize_btn.disabled = False
        if self.__can_review_brain():
            brain_btn.disabled = False

    def __can_finalize(self):
        id, tp = self.subject.split("|")
        labels_path = os.path.join(self.contents_path, id, tp)
        filename = f"{id}_{tp}_{DEFAULT_SEGMENTATION}"
        under_review_filepath = os.path.join(
            labels_path,
            "under_review",
            filename,
        )

        return os.path.exists(under_review_filepath)

    def __can_review_brain(self):
        id, tp = self.subject.split("|")
        filepath = os.path.join(self.contents_path, id, tp, BRAINMASK)

        return os.path.exists(filepath) and is_editor_installed(self.review_cmd)

    def __review_tumor(self):
        id, tp = self.subject.split("|")
        data_path = os.path.join(self.contents_path, id, tp, "brain_scans")
        labels_path = os.path.join(self.contents_path, id, tp)
        review_tumor(self.subject, data_path, labels_path, review_cmd=self.review_cmd)

    def __review_brainmask(self):
        id, tp = self.subject.split("|")
        data_path = os.path.join(self.contents_path, id, tp, "raw_scans")
        labels_path = os.path.join(self.contents_path, id, tp)
        review_brain(self.subject, labels_path, self.review_cmd, data_path)

    def __finalize(self):
        id, tp = self.subject.split("|")
        labels_path = os.path.join(self.contents_path, id, tp)
        finalize(self.subject, labels_path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        review_brainmask_button = self.query_one(".brain-btn", Button)
        review_button = self.query_one(".tumor-btn", Button)
        reviewed_button = self.query_one(".finalize-btn", Button)

        if event.control == review_brainmask_button:
            self.__review_brainmask()
        elif event.control == review_button:
            self.__review_tumor()
        elif event.control == reviewed_button:
            self.__finalize()

        self.__update_buttons()

    def __brain_has_been_reviewed(self):
        id, tp = self.subject.split("|")
        brainpath = os.path.join(self.contents_path, id, tp, BRAINMASK)
        backup_brainpath = os.path.join(self.contents_path, id, tp, BRAINMASK_BAK)

        if not os.path.exists(backup_brainpath):
            return False

        brain_hash = get_hash(brainpath)
        backup_hash = get_hash(backup_brainpath)
        return brain_hash != backup_hash

    def __tumor_has_been_finalized(self):
        id, tp = self.subject.split("|")
        finalized_tumor_path = os.path.join(self.contents_path, id, tp, "finalized")
        finalized_files = os.listdir(finalized_tumor_path)
        finalized_files = [file for file in finalized_files if not file.startswith(".")]

        return len(finalized_files) > 0
