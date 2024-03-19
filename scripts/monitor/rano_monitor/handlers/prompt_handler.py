import os
from watchdog.events import FileSystemEventHandler


class PromptHandler(FileSystemEventHandler):
    def __init__(self, dset_data_path: str, textual_app):
        self.dset_data_path = dset_data_path
        self.prompt_path = os.path.join(dset_data_path, ".prompt.txt")
        self.app = textual_app

    def manual_execute(self):
        if os.path.exists(self.prompt_path):
            self.display_prompt()

    def on_created(self, event):
        if event.src_path == self.prompt_path:
            if os.path.exists(event.src_path):
                self.display_prompt()

    def on_modified(self, event):
        self.on_created(event)

    def display_prompt(self):
        with open(self.prompt_path, "r") as f:
            prompt = f.read()
        self.app.update_prompt(prompt)
        # _confirm_dset(self.manager, prompt, self.dset_data_path)
