from watchdog.events import FileSystemEventHandler
import re
from rano_monitor.constants import *
from rano_monitor.utils import get_hash

class TarballReviewedHandler(FileSystemEventHandler):
    def __init__(self, contents_path: str, textual_app):
        self.contents_path = contents_path
        self.app = textual_app

    def on_modified(self, event):
        self.on_created(event)

    def on_created(self, event):
        is_tumor = os.path.basename(event.src_path).endswith(DEFAULT_SEGMENTATION)
        is_final = os.path.dirname(event.src_path).endswith("finalized")
        is_brain = os.path.basename(event.src_path) == BRAINMASK
        if (is_tumor and is_final) or is_brain:
            self.app.update_subjects_status()