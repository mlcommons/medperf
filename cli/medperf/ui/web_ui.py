from queue import Queue
from contextlib import contextmanager
from yaspin import yaspin
import typer

from medperf.ui.cli import CLI


class WebUI(CLI):
    def __init__(self):
        super().__init__()
        self.events: Queue[dict] = Queue()
        self.responses: Queue[dict] = Queue()
        self.is_interactive = False
        self.spinner = yaspin(color="green")

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
        # TODO: Check if there should be a better approach
        if "{" in msg and "}" in msg and ":" in msg:
            msg = msg.replace("=" * 20, "")
            type = "json"
        if "=" * 20 in msg:
            msg = msg.replace("=" * 20, "").strip()
            import yaml

            msg = yaml.dump(msg)
            type = "json"  # YAML

        if self.is_interactive:
            self.spinner.write(msg)
        else:
            typer.echo(msg)

        self.set_event({"type": type, "message": msg, "end": False})

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
        if not self.is_interactive:
            self.print(msg)

        self.set_event({"type": "text", "message": msg, "end": False})
        self.spinner.text = msg  # TODO

    def prompt(self, msg: str) -> str:
        """Displays a prompt to the user and waits for an answer

        Args:
            msg (str): message to use for the prompt

        Returns:
            str: user input
        """
        msg = msg.replace(" [Y/n]", "")
        self.set_event({"type": "prompt", "message": msg, "end": False})
        resp = self.get_response()
        if resp["value"]:
            return "y"
        return "n"

    def hidden_prompt(self, msg: str) -> str:
        """Displays a prompt to the user and waits for an aswer. User input is not displayed

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

    def set_event(self, dict):
        self.events.put(dict)

    def get_event(self):
        return self.events.get()

    def set_response(self, dict):
        self.responses.put(dict)

    def get_response(self):
        return self.responses.get()

    def set_success(self):
        self.events.put({"type": "highlight", "message": "&#x2705; Done", "end": True})

    def set_error(self):
        self.events.put(
            {"type": "highlight", "message": "&#x274C; Stopped", "end": True}
        )
