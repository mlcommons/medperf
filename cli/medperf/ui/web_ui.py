import json
from queue import Queue
from contextlib import contextmanager
from typing import Generator, Optional

import typer

from medperf.ui.cli import CLI

import asyncio


class WebUI(CLI):
    def __init__(self):
        super().__init__()
        self.message_queue: Queue[Optional[str]] = Queue()
        self.events: asyncio.Queue[dict] = Queue()  # Or just use Queue()
        self.responses: asyncio.Queue[dict] = Queue()  # Or just use Queue()
        self._is_proxy = False

    def start_proxy(self):
        self._is_proxy = True

    def stop_proxy(self):
        self.message_queue.put(None)
        self._is_proxy = False

    @contextmanager
    def proxy(self):
        self.start_proxy()
        try:
            yield self
        finally:
            self.stop_proxy()

    def get_message_generator(self) -> Generator[str, None, None]:
        while True:
            msg = self.message_queue.get()  # Block until a message is available
            if msg is None:
                break
            yield msg

    @property
    def text(self):
        return self.spinner.text

    @text.setter
    def text(self, msg: str = ""):
        """Displays a message that overwrites previous messages if they
        were created during an interactive ui session.

        If not on interactive session already, then it calls the ui print function

        Args:
            msg (str): message to display
        """
        if not self.is_interactive:
            self.print(msg)

        if self._is_proxy:
            self.message_queue.put(json.dumps({"type": "text", "message": msg}))
        self.spinner.text = msg

    def _print(self, msg: str = ""):
        if self.is_interactive:
            self.spinner.write(msg)
        else:
            typer.echo(msg)

        if self._is_proxy:
            self.message_queue.put(json.dumps({"type": "print", "message": msg}))

    def set_event(self, dict):
        self.events.put(dict)

    def get_event(self):
        return self.events.get()

    def set_response(self, dict):
        self.responses.put(dict)

    def get_response(self):
        return self.responses.get()

    def prompt(self, msg):
        self.set_event({"type": "prompt", "message": msg})
        self.set_event(None)
        resp = self.get_response()
        if resp["value"]:
            return "y"
        return "n"

    def print(self, msg=""):
        self.set_event({"type": "text", "message": msg})

    def print_warning(self, msg):
        self.set_event({"type": "warning", "message": msg})
