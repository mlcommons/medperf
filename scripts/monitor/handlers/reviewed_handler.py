import os
from watchdog.events import FileSystemEventHandler
from rano_monitor.constants import *
import tarfile
import re
from rano_monitor.utils import delete

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

