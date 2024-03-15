import os

from rano_monitor.constants import BRAINMASK, DEFAULT_SEGMENTATION
from watchdog.events import FileSystemEventHandler


class TarballReviewedHandler(FileSystemEventHandler):
    def __init__(self, contents_path: str, textual_app):
        self.contents_path = contents_path
        self.app = textual_app

    def on_modified(self, event):
        self.on_created(event)

    def on_created(self, event):
        src_path = event.src_path
        is_tumor = os.path.basename(src_path).endswith(DEFAULT_SEGMENTATION)
        is_final = os.path.dirname(src_path).endswith("finalized")
        is_brain = os.path.basename(src_path) == BRAINMASK
        if (is_tumor and is_final) or is_brain:
            self.app.update_subjects_status()
