import os

import pandas as pd
from rano_monitor.constants import (
    DEFAULT_SEGMENTATION,
    DONE_STAGE,
    MANUAL_REVIEW_STAGE,
)
from rano_monitor.messages import InvalidSubjectsUpdated
from rano_monitor.utils import (
    finalize,
    get_brain_path,
    is_editor_installed,
    review_brain,
    review_tumor,
    to_local_path,
)
from rano_monitor.widgets.copyable_item import CopyableItem
from textual.app import ComposeResult
from textual.containers import Center
from textual.widgets import Button, Markdown, Static


class SubjectDetails(Static):
    invalid_subjects = set()
    subject = pd.Series()
    dset_path = ""
    review_cmd = None # This will be assigned after initialized

    def compose(self) -> ComposeResult:
        with Center(id="subject-title"):
            yield Static(id="subject-name")
            yield Static(id="subject-status")
            yield Static(id="docs-url")
        yield Markdown(id="subject-comment-md")
        yield CopyableItem("Data path", "", id="subject-data-container")
        yield CopyableItem("Labels path", "", id="subject-labels-container")
        with Center(id="review-buttons"):
            yield Static(
                "ITK-Snap command-line-tools were not found in your system",
                id="review-msg",
                classes="warning",
            )
            yield Button(
                "Review Tumor Segmentation",
                variant="primary",
                disabled=True,
                id="review-button",
            )
            yield Button.success(
                "Mark as finalized (must review first)",
                id="reviewed-button",
                disabled=True,
            )
            yield Static(
                "If brain mask is not correct",
                id="brianmask-review-header"
            )
            yield Button(
                "Brain mask not available",
                disabled=True,
                id="brainmask-review-button",
            )
            yield Static(
                "IMPORTANT: Changes to the brain mask will "
                "invalidate tumor segmentations and cause a "
                "re-run of tumor segmentation models",
                id="brainmask-review-warning",
                classes="warning",
            )
        yield Button("Invalidate", id="valid-btn")

    def on_invalid_subjects_updated(self, message: InvalidSubjectsUpdated):
        self.invalid_subjects = message.invalid_subjects
        self.update_subject()

    def set_invalid_path(self, invalid_path):
        self.invalid_path = invalid_path

    def update_subject(self):
        subject = self.subject
        dset_path = self.dset_path
        if subject.empty:
            return
        wname = self.query_one("#subject-name", Static)
        wstatus = self.query_one("#subject-status", Static)
        wdocs = self.query_one("#docs-url", Static)
        wmsg = self.query_one("#subject-comment-md", Markdown)
        wdata = self.query_one("#subject-data-container", CopyableItem)
        wlabels = self.query_one("#subject-labels-container", CopyableItem)
        buttons_container = self.query_one("#review-buttons", Center)

        labels_path = os.path.join(dset_path, "../labels")
        if subject["status_name"] != "DONE":
            # Hard coding some behavior from the RANO data prep cube.
            # This is because for the most part, the labels live within
            # the data path right until the end
            # This SHOULD NOT be here for general data prep monitoring
            labels_path = dset_path
        wname.update(subject.name)
        wstatus.update(subject["status_name"])
        wmsg.update(subject["comment"])
        if subject.name in self.invalid_subjects:
            msg = "Subject has been invalidated and will be skipped from the "
            "preparation procedure. If you want to include the subject again, "
            "revalidate it"
            wstatus.update("INVALIDATED")
            wmsg.update(msg)
        wdata.update(to_local_path(subject["data_path"], dset_path))
        wlabels.update(to_local_path(subject["labels_path"], labels_path))
        if subject["docs_url"]:
            url = subject["docs_url"]
            ln = f"Full documentation: [@click=app.open_url('{url}')]{url}[/]"
            wdocs.update(ln)
        else:
            wdocs.display = "none"

        # Hardcoding manual review behavior.
        # This SHOULD NOT be here for general data prep monitoring.
        # Additional configuration must be set
        # to make this kind of features generic
        can_review = MANUAL_REVIEW_STAGE <= abs(subject["status"]) < DONE_STAGE
        buttons_container.display = "block" if can_review else "none"

        # Only display finalize button for the manual review
        can_finalize = abs(subject["status"]) == MANUAL_REVIEW_STAGE
        reviewed_button = self.query_one("#reviewed-button", Button)
        reviewed_button.display = "block" if can_finalize else "none"

        self.__update_buttons()

    def __update_buttons(self):
        review_msg = self.query_one("#review-msg", Static)
        review_button = self.query_one("#review-button", Button)
        reviewed_button = self.query_one("#reviewed-button", Button)
        brainmask_button = self.query_one("#brainmask-review-button", Button)
        valid_btn = self.query_one("#valid-btn", Button)

        if is_editor_installed(self.review_cmd):
            review_msg.display = "none"
            review_button.disabled = False
        if self.__can_finalize():
            reviewed_button.label = "Mark as finalized"
            reviewed_button.disabled = False
        if self.__can_review_brain():
            brainmask_button.label = "Review brain mask"
            brainmask_button.disabled = False
        if self.subject.name in self.invalid_subjects:
            valid_btn.label = "Validate"
        else:
            valid_btn.label = "Invalidate"

    def __can_finalize(self):
        labels_path = self.subject["labels_path"]
        labels_path = to_local_path(labels_path, self.dset_path)
        id, tp = self.subject.name.split("|")
        filename = f"{id}_{tp}_{DEFAULT_SEGMENTATION}"
        under_review_filepath = os.path.join(
            labels_path,
            "under_review",
            filename,
        )

        return os.path.exists(under_review_filepath)

    def __can_review_brain(self):
        labels_path = self.subject["labels_path"]
        labels_path = to_local_path(labels_path, self.dset_path)
        if self.subject["labels_path"]:
            brainmask_file = get_brain_path(labels_path)
            return os.path.exists(brainmask_file)
        return False

    def __review_tumor(self):
        subject = self.subject.name
        data_path = self.subject["data_path"]
        data_path = to_local_path(data_path, self.dset_path)
        labels_path = self.subject["labels_path"]
        labels_path = to_local_path(labels_path, self.dset_path)
        review_tumor(subject, data_path, labels_path, review_cmd=self.review_cmd)
        self.__update_buttons()
        self.notify("This subject can be finalized now")

    def __review_brainmask(self):
        subject = self.subject.name
        labels_path = self.subject["labels_path"]
        labels_path = to_local_path(labels_path, self.dset_path)
        review_brain(subject, labels_path, review_cmd=self.review_cmd)
        self.__update_buttons()

    def __finalize(self):
        subject = self.subject.name
        labels_path = self.subject["labels_path"]
        labels_path = to_local_path(labels_path, self.dset_path)
        finalize(subject, labels_path)
        self.notify("Subject finalized")

    def __validate(self):
        with open(self.invalid_path, "r") as f:
            invalid_subjects = set([id.strip() for id in f.readlines()])
        if self.subject.name not in invalid_subjects:
            return

        invalid_subjects.remove(self.subject.name)
        with open(self.invalid_path, "w") as f:
            f.write("\n".join(invalid_subjects))

    def __invalidate(self):
        with open(self.invalid_path, "r") as f:
            invalid_subjects = set([id.strip() for id in f.readlines()])
        if self.subject.name in invalid_subjects:
            return

        invalid_subjects.add(self.subject.name)
        with open(self.invalid_path, "w") as f:
            f.write("\n".join(invalid_subjects))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        review_brain_btn = self.query_one("#brainmask-review-button", Button)
        review_button = self.query_one("#review-button", Button)
        reviewed_button = self.query_one("#reviewed-button", Button)
        validate_button = self.query_one("#valid-btn", Button)

        if event.control == review_brain_btn:
            self.__review_brainmask()
        elif event.control == review_button:
            self.__review_tumor()
        elif event.control == reviewed_button:
            self.__finalize()
        elif event.control == validate_button:
            if self.subject.name in self.invalid_subjects:
                self.__validate()
            else:
                self.__invalidate()

        self.__update_buttons()
