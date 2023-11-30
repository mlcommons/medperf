"""
Code browser example.

Run with:

    python code_browser.py PATH
"""

import os
import re
import shutil
from pathlib import Path
import typer
import pyperclip
from tabulate import tabulate
from typer import Argument, Option
from medperf.utils import storage_path, read_config, set_custom_config
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from medperf import config
import yaml
import pandas as pd
import tarfile
from subprocess import Popen, DEVNULL

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
    Markdown,
)

NAME_HELP = "The name of the dataset to monitor"
MLCUBE_HELP = "The Data Preparation MLCube UID used to create the data"
STAGES_HELP = "Path to stages YAML file containing documentation about the Data Preparation stages"
DEFAULT_SEGMENTATION = "tumorMask_fused-staple.nii.gz"
DEFAULT_STAGES_PATH = os.path.join(os.path.dirname(__file__), "assets/stages.yaml")
BRAINMASK = "brainMask_fused.nii.gz"
REVIEW_FILENAME = "review_cases.tar.gz"
REVIEW_COMMAND = "itksnap"
MANUAL_REVIEW_STAGE = 5
DONE_STAGE = 8
LISTITEM_MAX_LEN = 30


def generate_full_report(report_dict: dict, stages_path: str):
    with open(stages_path, "r") as f:
        stages = yaml.safe_load(f)

    report_keys = ["comment", "status_name", "docs_url", "status"]
    for key in report_keys:
        if key not in report_dict:
            report_dict[key] = {}

    for case, status in report_dict["status"].items():
        stage = stages[status]
        for key, val in stage.items():
            # First make sure to populate the stage key for missing cases
            if case not in report_dict[key]:
                report_dict[key][case] = ""
            # Then, if the stage contains information for that key, add it
            if val is not None:
                report_dict[key][case] = val

    return report_dict


def delete(filepath: str, dset_path: str):
    try:
        os.remove(filepath)
        return
    except PermissionError:
        pass

    # Handle scenarios where user doesn't have permission to delete stuff
    # Instead, move the file-of-interest to a trash folder so that it can be
    # deleted by the MLCube, with proper permissions
    trash_path = os.path.join(dset_path, ".trash")
    os.makedirs(trash_path, exist_ok=True)
    num_trashfiles = len(os.listdir(trash_path))

    # Rename the file to the number of files. This is to avoid collisions
    target_filepath = os.path.join(trash_path, str(num_trashfiles))
    shutil.move(filepath, target_filepath)


def to_local_path(mlcube_path: str, local_parent_path: str):
    if not isinstance(mlcube_path, str):
        return mlcube_path
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
    with tarfile.open(REVIEW_FILENAME, "w:gz") as tar:
        for i, row in review_cases.iterrows():
            labels_path = to_local_path(row["labels_path"], dset_path)
            base_path = os.path.join(labels_path, "..")

            # Add tumor segmentations
            id, tp = row.name.split("|")
            tar_path = os.path.join("review_cases", id, tp)
            reviewed_path = os.path.join("review_cases", id, tp, "finalized")
            reviewed_dir = tarfile.TarInfo(name=reviewed_path)
            reviewed_dir.type = tarfile.DIRTYPE
            reviewed_dir.mode = 0o755
            tar.addfile(reviewed_dir)
            tar.add(labels_path, tar_path)

            # Add brain mask
            brain_mask_filename = "brainMask_fused.nii.gz"
            brain_mask_path = os.path.join(base_path, brain_mask_filename)
            brain_mask_tar_path = os.path.join(tar_path, brain_mask_filename)
            tar.add(brain_mask_path, brain_mask_tar_path)

            # Add summary images
            for file in os.listdir(base_path):
                if not file.endswith(".png"):
                    continue
                img_path = os.path.join(base_path, file)
                img_tar_path = os.path.join(tar_path, file)
                tar.add(img_path, img_tar_path)


class ReportState:
    def __init__(self, report_path: str, app):
        self.report_path = report_path
        self.app = app
        self.report = None

    def update(self):
        with open(self.report_path, "r") as f:
            report_dict = yaml.safe_load(f)

        if report_dict is not None and len(report_dict):
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


class ReviewedHandler(FileSystemEventHandler):
    def __init__(self, dset_data_path: str, textual_app):
        self.dset_data_path = dset_data_path
        self.app = textual_app
        self.ext = ".tar.gz"

        for file in os.listdir("."):
            if file.endswith(self.ext):
                self.move_assets(file)

    def on_modified(self, event):
        if os.path.basename(event.src_path) == REVIEW_FILENAME:
            return
        if event.src_path.endswith(self.ext):
            self.move_assets(event.src_path)

    def move_assets(self, file):
        reviewed_pattern = r".*\/(.*)\/(.*)\/finalized\/(.*\.nii\.gz)"
        brainmask_pattern = r".*\/(.*)\/(.*)\/brainMask_fused.nii.gz"
        identified_reviewed = []
        identified_brainmasks = []
        try:
            with tarfile.open(file, "r") as tar:
                for member in tar.getmembers():
                    review_match = re.match(reviewed_pattern, member.name)
                    if review_match:
                        identified_reviewed.append(review_match)

                    brainmask_match = re.match(brainmask_pattern, member.name)
                    if brainmask_match:
                        identified_brainmasks.append(brainmask_match)
        except:
            return

        if len(identified_reviewed):
            self.app.notify("Reviewed cases identified")

        extracts = []
        for reviewed in identified_reviewed:
            id, tp, filename = reviewed.groups()
            src_path = reviewed.group(0)
            dest_path = os.path.join(
                self.dset_data_path,
                "tumor_extracted",
                "DataForQC",
                id,
                tp,
                "TumorMasksForQC",
                "finalized",
            )
            if not os.path.exists(dest_path):
                # Don't try to add reviewed file if the dest path
                # doesn't exist
                continue

            # dest_path = os.path.join(dest_path, filename)
            extracts.append((src_path, dest_path))

        if len(identified_brainmasks):
            self.app.notify("Brain masks identified")

        for mask in identified_brainmasks:
            id, tp = mask.groups()
            src_path = mask.group(0)
            dest_path = os.path.join(
                self.dset_data_path,
                "tumor_extracted",
                "DataForQC",
                id,
                tp,
            )
            extracts.append((src_path, dest_path))

        with tarfile.open(file, "r") as tar:
            for src, dest in extracts:
                member = tar.getmember(src)
                member.name = os.path.basename(member.name)
                target_file = os.path.join(dest, member.name)
                # TODO: this might be problematic UX. The brainmask might get overwritten without the user aknowledging it
                if os.path.exists(target_file):
                    delete(target_file, self.dset_data_path)
                tar.extract(member, dest)


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
            yield Button("package cases for review", id="package-btn")

    def set_reviewed_watchdog(self, reviewed_watchdog: ReviewedHandler):
        self.reviewed_watchdog = reviewed_watchdog

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
        self.notify(f"{REVIEW_FILENAME} was created on the working directory")


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
        yield Button("Copy", classes="subject-item-copy")

    def update(self, content):
        self.content = content

    def watch_content(self, content):
        if not isinstance(content, str) or len(content) == 0:
            self.display = False
            return
        subject = self.query_one(".subject-item-content", Static)
        subject.update(content)
        self.display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        try:
            pyperclip.copy(self.content)
            self.notify("Text copied to clipboard")
        except pyperclip.PyperclipException:
            with open("clipboard.txt", "w") as f:
                f.write(self.content)
            self.notify(
                "Clipboard not supported on your machine. Contents copied to clipboard.txt",
                severity="warning",
            )


class SubjectDetails(Static):
    def compose(self) -> ComposeResult:
        with Center(id="subject-title"):
            yield Static(id="subject-name")
            yield Static(id="subject-status")
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
            yield Static("If brain mask is not correct")
            yield Button(
                "Review Brain Mask",
                disabled=True,
                id="brainmask-review-button",
            )
            yield Static(
                "IMPORTANT: Changes to the brain mask will invalidate tumor segmentations and cause a re-run of tumor segmentation models",
                classes="warning",
            )

    def update_subject(self, subject: pd.Series, dset_path: str):
        self.subject = subject
        self.dset_path = dset_path
        wname = self.query_one("#subject-name", Static)
        wstatus = self.query_one("#subject-status", Static)
        wmsg = self.query_one("#subject-comment-md", Markdown)
        wdata = self.query_one("#subject-data-container", CopyableItem)
        wlabels = self.query_one("#subject-labels-container", CopyableItem)
        buttons_container = self.query_one("#review-buttons", Center)

        labels_path = os.path.join(dset_path, "../labels")
        if subject["status_name"] != "DONE":
            # Hard coding some behavior from the RANO data prep cube. This is because
            # for the most part, the labels live within the data path right until the end
            # This SHOULD NOT be here for general data prep monitoring
            labels_path = dset_path
        wname.update(subject.name)
        wstatus.update(subject["status_name"])
        wmsg.update(subject["comment"])
        wdata.update(to_local_path(subject["data_path"], dset_path))
        wlabels.update(to_local_path(subject["labels_path"], labels_path))
        # Hardcoding manual review behavior. This SHOULD NOT be here for general data prep monitoring.
        # Additional configuration must be set to make this kind of features generic
        can_review = MANUAL_REVIEW_STAGE <= abs(subject["status"]) < DONE_STAGE
        buttons_container.display = "block" if can_review else "none"

        # Only display finalize button for the manual review
        can_finalize = abs(subject["status"]) == MANUAL_REVIEW_STAGE
        reviewed_button = self.query_one("#reviewed-button", Button)
        reviewed_button.display = "block" if can_finalize else "none"

        self.__update_buttons()

    def __update_buttons(self):
        review_msg = self.query_one("#review-msg", Static)
        review_brainmask_button = self.query_one("#brainmask-review-button", Button)
        review_button = self.query_one("#review-button", Button)
        reviewed_button = self.query_one("#reviewed-button", Button)

        if self.__can_review():
            review_msg.display = "none"
            review_brainmask_button.disabled = False
            review_button.disabled = False
        if self.__can_finalize():
            reviewed_button.label = "Mark as finalized"
            reviewed_button.disabled = False

    def __can_review(self):
        review_command_path = shutil.which(REVIEW_COMMAND)
        return review_command_path is not None

    def __can_finalize(self):
        labels_path = to_local_path(self.subject["labels_path"], self.dset_path)
        id, tp = self.subject.name.split("|")
        filename = f"{id}_{tp}_{DEFAULT_SEGMENTATION}"
        under_review_filepath = os.path.join(
            labels_path,
            "under_review",
            filename,
        )

        return os.path.exists(under_review_filepath)

    def __review_tumor(self):
        review_cmd = "{cmd} -g {t1c} -o {flair} {t2} {t1} -s {seg} -l {label}"
        data_path = to_local_path(self.subject["data_path"], self.dset_path)
        labels_path = to_local_path(self.subject["labels_path"], self.dset_path)

        id, tp = self.subject.name.split("|")
        t1c_file = os.path.join(data_path, f"{id}_{tp}_brain_t1c.nii.gz")
        t1n_file = os.path.join(data_path, f"{id}_{tp}_brain_t1n.nii.gz")
        t2f_file = os.path.join(data_path, f"{id}_{tp}_brain_t2f.nii.gz")
        t2w_file = os.path.join(data_path, f"{id}_{tp}_brain_t2w.nii.gz")
        label_file = os.path.join(os.path.dirname(__file__), "assets/postop_gbm.label")

        if labels_path.endswith(".nii.gz"):
            seg_filename = os.path.basename(labels_path)
            seg_file = labels_path
            under_review_file = labels_path
        else:
            seg_filename = f"{id}_{tp}_{DEFAULT_SEGMENTATION}"
            seg_file = os.path.join(labels_path, seg_filename)
            under_review_file = os.path.join(
                labels_path,
                "under_review",
                seg_filename,
            )
            if not os.path.exists(under_review_file):
                shutil.copyfile(seg_file, under_review_file)

        review_cmd = review_cmd.format(
            cmd=REVIEW_COMMAND,
            t1c=t1c_file,
            flair=t2f_file,
            t2=t2w_file,
            t1=t1n_file,
            seg=under_review_file,
            label=label_file,
        )
        Popen(review_cmd.split(), shell=False, stdout=DEVNULL, stderr=DEVNULL)

        self.__update_buttons()
        self.notify("This subject can be finalized now")

    def __review_brainmask(self):
        review_cmd = "{cmd} -g {t1c} -o {flair} {t2} {t1} -s {seg} -l {label}"
        labels_path = to_local_path(self.subject["labels_path"], self.dset_path)
        if labels_path.endswith(".nii.gz"):
            # We are past manual review, transform the path as necessary
            labels_path = os.path.dirname(labels_path)
            labels_path = os.path.join(labels_path, "..")
        labels_path = os.path.join(labels_path, "..")
        data_path = os.path.join(labels_path, "reoriented")
        id, tp = self.subject.name.split("|")
        seg_filename = BRAINMASK
        seg_file = os.path.join(labels_path, seg_filename)
        t1c_file = os.path.join(data_path, f"{id}_{tp}_t1c.nii.gz")
        t1n_file = os.path.join(data_path, f"{id}_{tp}_t1.nii.gz")
        t2f_file = os.path.join(data_path, f"{id}_{tp}_t2f.nii.gz")
        t2w_file = os.path.join(data_path, f"{id}_{tp}_t2w.nii.gz")
        label_file = os.path.join(os.path.dirname(__file__), "assets/brainmask.label")

        review_cmd = review_cmd.format(
            cmd=REVIEW_COMMAND,
            t1c=t1c_file,
            flair=t2f_file,
            t2=t2w_file,
            t1=t1n_file,
            seg=seg_file,
            label=label_file,
        )
        Popen(review_cmd.split(), shell=False, stdout=DEVNULL, stderr=DEVNULL)

        self.__update_buttons()

    def __finalize(self):
        labels_path = to_local_path(self.subject["labels_path"], self.dset_path)
        id, tp = self.subject.name.split("|")
        filename = f"{id}_{tp}_{DEFAULT_SEGMENTATION}"
        under_review_filepath = os.path.join(
            labels_path,
            "under_review",
            filename,
        )
        finalized_filepath = os.path.join(labels_path, "finalized", filename)
        shutil.copyfile(under_review_filepath, finalized_filepath)
        self.notify("Subject finalized")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        review_brainmask_button = self.query_one("#brainmask-review-button", Button)
        review_button = self.query_one("#review-button", Button)
        reviewed_button = self.query_one("#reviewed-button", Button)

        if event.control == review_brainmask_button:
            self.__review_brainmask()
        elif event.control == review_button:
            self.__review_tumor()
        elif event.control == reviewed_button:
            self.__finalize()


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

    def set_stages_path(self, stages_path: str):
        self.stages_path = stages_path

    def set_reviewed_watchdog(self, reviewed_watchdog: ReviewedHandler):
        self.reviewed_watchdog = reviewed_watchdog

    def set_output_path(self, output_path: str):
        self.output_path = output_path

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

        # Set title - subtitle
        self.title = "Subject Browser"
        self.sub_title = os.getcwd()

        # Load report for the first time
        report_path = os.path.join(self.dset_data_path, "..", "report.yaml")
        if os.path.exists(report_path):
            with open(report_path, "r") as f:
                self.report = yaml.safe_load(f)

        # Set reviewed watchdog for summary view
        summary = self.query_one("#summary", Summary)
        summary.set_reviewed_watchdog(self.reviewed_watchdog)

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
        except:
            return


def main(
    name: str = Argument(..., help=NAME_HELP),
    mlcube_uid: int = Argument(..., help=MLCUBE_HELP),
    stages_path: str = Option(DEFAULT_STAGES_PATH, help=STAGES_HELP),
    output_path: str = Option(None, "-o", "--out", help="CSV file to store report in"),
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
    app.set_stages_path(stages_path)
    app.set_output_path(output_path)

    report_state = ReportState(report_path, app)
    report_watchdog = ReportHandler(report_state)
    prompt_watchdog = PromptHandler(dset_data_path, app)
    reviewed_watchdog = ReviewedHandler(dset_data_path, app)

    app.set_reviewed_watchdog(reviewed_watchdog)

    observer = Observer()
    observer.schedule(report_watchdog, dset_path)
    observer.schedule(prompt_watchdog, os.path.join(dset_path, "data"))
    observer.schedule(reviewed_watchdog, ".")
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
