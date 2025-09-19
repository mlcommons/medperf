import json
from queue import Queue
from contextlib import contextmanager
import threading
import time
from typing import List
from medperf.web_ui.common import add_notification
from yaspin import yaspin
import typer

from medperf.ui.cli import CLI
from medperf.web_ui.schemas import EventBase, Event, EventChunk

MAX_CHUNK_LENGTH = 20  # Max 20 events in a chunk
MAX_CHUNK_SIZE = 64 * 1024  # Max 64 Bytes as chunk size
MAX_CHUNK_AGE = 2.0  # Max 2 seconds as age of a chunk


class WebUI(CLI):
    def __init__(self):
        super().__init__()
        self.events: Queue[EventBase] = Queue()
        self.responses: Queue[dict] = Queue()
        self.is_interactive = False
        self.spinner = yaspin(color="green")
        self.task_id = None
        self.request = None

        # For Creating Chunks
        self.buffer: List[Event] = []
        self.b_size = 0  # For bytes check
        self.b_created_at = 0  # For age check - will be time.monotonic()
        self.b_lock = threading.Lock()
        self.b_stop_event = threading.Event()

    def is_chunkable(self, event: Event) -> bool:
        """Return True if the event should be combined into a print chunk.

        Chunking applies only to interactive print lines.

        Args:
            event: The event object.

        Returns:
            bool: True if this event is an interactive print - False otherwise.
        """
        return event.interactive and event.type == "print"

    def event_size_bytes(self, event: Event) -> int:
        event_string = json.dumps(
            event.to_json(), ensure_ascii=False, separators=(",", ":")
        )
        return len(event_string.encode("utf-8"))

    def add_to_buffer(self, event: Event):
        """Append an event to the current chunk buffer and update buffer size.

        Starts the age timer if the buffer was previously empty.

        Args:
            event: The event to buffer (typically an interactive print line).
        """

        if not self.buffer:
            self.b_created_at = time.monotonic()
        self.buffer.append(event)
        self.b_size += self.event_size_bytes(event)

    def _build_chunk(self, events: List[Event], size: int) -> EventChunk:
        for i, ev in enumerate(events, 1):
            ev.id = i

        return EventChunk(
            task_id=self.task_id,
            events=events,
            length=len(events),
            size_bytes=size,
        )

    def flush_buffer(self):
        """Emit the current chunk as an EventChunk and reset the buffer."""

        if not self.buffer:
            return
        buffer = list(self.buffer)
        size = self.b_size
        self.buffer.clear()
        self.b_size = 0
        self.b_created_at = 0

        if len(buffer) != 1:
            chunk = self._build_chunk(buffer, size)
            self.events.put_nowait(chunk)
            return

        self.events.put_nowait(buffer[0])

    def flush_buffer_by_size(self):
        """Flush the buffer if it exceeds length / size(bytes) thresholds."""
        length_exceeded = len(self.buffer) >= MAX_CHUNK_LENGTH
        size_bytes_exceeded = self.b_size >= MAX_CHUNK_SIZE

        if self.buffer and (length_exceeded or size_bytes_exceeded):
            self.flush_buffer()

    def flush_buffer_by_age(self):
        """Flush the buffered events if the oldest entry exceeds the age threshold."""
        time_exceeded = (time.monotonic() - self.b_created_at) >= MAX_CHUNK_AGE
        if self.buffer and time_exceeded:
            self.flush_buffer()

    def flush_by_age_worker(self):
        """Run a background loop that flushes the chunk buffer when it exceeds the max age.

        Runs until 'b_stop_event' is set.
        """
        while not self.b_stop_event.is_set():
            with self.b_lock:
                self.flush_buffer_by_age()
            time.sleep(0.2)

    def start_buffering(self):
        """Start the age-flush worker"""
        self.b_stop_event.clear()

        # worker for age-flushing
        age_worker = threading.Thread(target=self.flush_by_age_worker, daemon=True)
        age_worker.start()

    def stop_buffering(self):
        """Signal the age-flush worker to stop, then flush any remaining buffered events."""
        self.b_stop_event.set()
        with self.b_lock:
            self.flush_buffer()

    def print(self, msg: str = ""):
        """Display a message on the command line

        Args:
            msg (str): message to print
        """
        self._print(msg, "print")

    def print_error(self, msg: str):
        """Display an error message on the command line

        Args:
            msg (str): error message to display
        """
        msg = f"❌ {msg}"
        msg = typer.style(msg, fg=typer.colors.RED, bold=True)
        self._print(msg, "error")

    def print_warning(self, msg: str):
        """Display a warning message on the command line

        Args:
            msg (str): warning message to display
        """
        msg = typer.style(msg, fg=typer.colors.YELLOW, bold=True)
        self._print(msg, "warning")

    def _print(self, msg: str = "", type: str = "print"):
        if self.is_interactive:
            self.spinner.write(msg)
        else:
            typer.echo(msg)

        self.set_event(
            Event(
                task_id=self.task_id,
                type=type,
                message=msg,
                interactive=self.is_interactive,
                end=False,
            )
        )

    def start_interactive(self):
        """Start an interactive session where messages can be overwritten
        and animations can be displayed"""
        self.is_interactive = True
        self.spinner.start()  # TODO

    def stop_interactive(self):
        """Stop an interactive session"""
        self.is_interactive = False
        self.spinner.stop()  # TODO

    @contextmanager
    def interactive(self):
        """Context managed interactive session.

        Yields:
            CLI: Yields the current CLI instance with an interactive session initialized
        """
        if self.is_interactive:
            # if already interactive, do nothing
            yield self
        else:
            self.start_interactive()
            try:
                yield self
            finally:
                self.stop_interactive()

    @property
    def text(self):
        return self.spinner.text  # TODO

    @text.setter
    def text(self, msg: str = ""):
        """Displays a message that overwrites previous messages if they
        were created during an interactive ui session.

        If not on interactive session already, then it calls the ui print function

        Args:
            msg (str): message to display
        """
        # if not self.is_interactive:
        #     self.print(msg)

        self.set_event(
            Event(
                task_id=self.task_id,
                type="text",
                message=msg,
                interactive=self.is_interactive,
                end=False,
            )
        )
        self.spinner.text = msg  # TODO

    def prompt(self, msg: str) -> str:
        """Displays a prompt to the user and waits for an answer

        Args:
            msg (str): message to use for the prompt

        Returns:
            str: user input
        """
        msg = msg.replace(" [Y/n]", "")
        self.set_event(
            Event(
                task_id=self.task_id,
                type="prompt",
                message=msg,
                interactive=self.is_interactive,
                end=False,
            )
        )
        add_notification(
            self.request,
            message="A prompt is waiting for your response in the current running task",
            return_response={"status": "info"},
        )
        resp = self.get_response()
        if resp["value"]:
            return "y"
        return "n"

    def hidden_prompt(self, msg: str) -> str:
        """Displays a prompt to the user and waits for an answer. User input is not displayed

        Args:
            msg (str): message to use for the prompt

        Returns:
            str: user input
        """
        return super().hidden_prompt()

    def print_highlight(self, msg: str = ""):
        """Display a highlighted message

        Args:
            msg (str): message to print
        """
        self._print(msg, "highlight")

    def print_yaml(self, msg: str):
        """Display a yaml object on the command line

        Args:
            msg (str): message to display
        """
        self._print(msg, "yaml")

    def print_url(self, msg: str):
        self._print(msg, "url")

    def print_code(self, msg: str):
        self._print(msg, "code")

    def set_event(self, event: Event):
        if self.is_chunkable(event):
            with self.b_lock:
                self.add_to_buffer(event)
                self.flush_buffer_by_size()
            return

        with self.b_lock:
            self.flush_buffer()

        self.events.put_nowait(event)

    def get_event(self, timeout=None):
        return self.events.get(block=True, timeout=timeout)

    def set_response(self, event):
        self.responses.put(event)

    def get_response(self):
        return self.responses.get()

    def end_task(self, response=None):
        self.stop_buffering()

        self.set_event(
            Event(
                task_id=self.task_id,
                type="highlight",
                message="",
                interactive=self.is_interactive,
                end=True,
                response=response,
            )
        )
        self.unset_task_id()
        self.unset_request()

    def start_task(self, task_id: str, request):
        self.set_task_id(task_id)
        self.set_request(request)
        self.start_buffering()

    def set_task_id(self, task_id):
        self.task_id = task_id

    def set_request(self, request):
        self.request = request

    def unset_request(self):
        self.request = None

    def unset_task_id(self):
        self.task_id = None
