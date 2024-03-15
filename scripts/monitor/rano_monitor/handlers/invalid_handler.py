import os
from watchdog.events import FileSystemEventHandler


class InvalidHandler(FileSystemEventHandler):
    def __init__(self, invalid_path: str, textual_app):
        self.invalid_path = invalid_path
        self.app = textual_app

    def manual_execute(self):
        if os.path.exists(self.invalid_path):
            self.update()

    def on_modified(self, event):
        if event.src_path == self.invalid_path:
            self.update()

    def update(self):
        with open(self.invalid_path, "r") as f:
            invalid_subjects = set([id.strip() for id in f.readlines()])
        self.app.update_invalid(invalid_subjects)
