import os
import re
import tarfile

from rano_monitor.constants import (
    BRAINMASK_PATTERN,
    REVIEW_FILENAME,
    REVIEWED_PATTERN,
    ANNOTATIONS_ENABLED
)
from rano_monitor.utils import delete
from watchdog.events import FileSystemEventHandler


def get_tar_identified_masks(file):
    identified_reviewed = []
    identified_brainmasks = []
    try:
        with tarfile.open(file, "r") as tar:
            for member in tar.getmembers():
                review_match = re.match(REVIEWED_PATTERN, member.name)
                if review_match:
                    identified_reviewed.append(review_match)

                brainmask_match = re.match(BRAINMASK_PATTERN, member.name)
                if brainmask_match:
                    identified_brainmasks.append(brainmask_match)
    except Exception:
        return [], []

    return identified_reviewed, identified_brainmasks


def get_identified_extract_paths(
        identified_reviewed,
        identified_brainmasks,
        dset_data_path
):
    extracts = []
    for reviewed in identified_reviewed:
        id, tp, filename = reviewed.groups()
        src_path = reviewed.group(0)
        dest_path = os.path.join(
            dset_data_path,
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

    for mask in identified_brainmasks:
        id, tp = mask.groups()
        src_path = mask.group(0)
        dest_path = os.path.join(
            dset_data_path,
            "tumor_extracted",
            "DataForQC",
            id,
            tp,
        )
        extracts.append((src_path, dest_path))

    return extracts


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
        if not ANNOTATIONS_ENABLED:
            return
        if event.src_path.endswith(self.ext):
            self.move_assets(event.src_path)

    def move_assets(self, file):
        identified_masks = get_tar_identified_masks(file)
        identified_reviewed, identified_brainmasks = identified_masks

        if len(identified_reviewed):
            self.app.notify("Reviewed cases identified")

        if len(identified_brainmasks):
            self.app.notify("Brain masks identified")

        extracts = get_identified_extract_paths(
            identified_reviewed,
            identified_brainmasks,
            self.dset_data_path
        )

        with tarfile.open(file, "r") as tar:
            for src, dest in extracts:
                member = tar.getmember(src)
                member.name = os.path.basename(member.name)
                target_file = os.path.join(dest, member.name)
                # TODO: this might be problematic UX.
                # The brainmask might get overwritten unknowingly
                if os.path.exists(target_file):
                    delete(target_file, self.dset_data_path)
                tar.extract(member, dest)
