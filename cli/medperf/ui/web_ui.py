from queue import Queue
from contextlib import contextmanager
from medperf.web_ui.common import add_notification
from yaspin import yaspin
import typer

from medperf.ui.cli import CLI
from medperf.web_ui.schemas import Event, EventsManager


class WebUI(CLI):
    def __init__(self):
        super().__init__()
        self.responses: Queue[dict] = Queue()
        self.is_interactive = False
        self.spinner = yaspin(color="green")
        self.task_id = None
        self.request = None
        self.events_manager = EventsManager()

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
        self.events_manager.process_event(event)

    def get_event(self, timeout=None):
        return self.events_manager.dequeue_event(timeout=timeout)

    def set_response(self, event):
        self.responses.put(event)

    def get_response(self):
        return self.responses.get()

    def end_task(self, response=None):
        self.events_manager.stop_buffering()

        self.events_manager.enqueue_event(
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
        self.events_manager.start_buffering()

    def set_task_id(self, task_id):
        self.task_id = task_id

    def set_request(self, request):
        self.request = request

    def unset_request(self):
        self.request = None

    def unset_task_id(self):
        self.task_id = None
