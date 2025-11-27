import re
import typer
from getpass import getpass
from yaspin import yaspin
from contextlib import contextmanager

from .interface import UI


class CLI(UI):
    def __init__(self):
        self.spinner = yaspin(color="green")
        self.is_interactive = False
        self.is_regex = False

    def print_url_message(self, message: str):
        match = re.search(r"https?://[^\s]+", message)

        url = match.group(0)
        start, end = match.span()

        before = message[:start].strip()
        after = message[end:].strip()

        if before.strip():
            self._print(before)

        self.print_url(url)

        if after.strip():
            self._print(after)

    def contains_url(self, message: str):
        return bool(re.search(r"https?://[^\s]+", message))

    def is_code(self, message: str):
        ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
        message = ansi_escape.sub("", message.strip())
        return bool(re.fullmatch(r"[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}", message))

    def print(self, msg: str = ""):
        """Display a message on the command line

        Args:
            msg (str): message to print
        """
        if self.is_regex:
            if self.is_code(msg):
                self.print_code(msg)
            elif self.contains_url(msg):
                self.print_url_message(msg)
            else:
                self._print(msg)
        else:
            self._print(msg)

    def print_error(self, msg: str):
        """Display an error message on the command line

        Args:
            msg (str): error message to display
        """
        msg = f"❌ {msg}"
        msg = typer.style(msg, fg=typer.colors.RED, bold=True)
        self._print(msg)

    def print_critical(self, msg: str):
        self.print_warning(msg)

    def print_warning(self, msg: str):
        """Display a warning message on the command line

        Args:
            msg (str): warning message to display
        """
        msg = typer.style(msg, fg=typer.colors.YELLOW, bold=True)
        self._print(msg)

    def print_url(self, msg: str):
        self._print(msg)

    def print_code(self, msg: str):
        self._print(msg)

    def _print(self, msg: str = ""):
        if self.is_interactive:
            self.spinner.write(msg)
        else:
            typer.echo(msg)

    def start_interactive(self):
        """Start an interactive session where messages can be overwritten
        and animations can be displayed"""
        self.is_interactive = True
        self.spinner.start()

    def stop_interactive(self):
        """Stop an interactive session"""
        self.is_interactive = False
        self.spinner.stop()

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

    def start_regex(self):
        """Start a regex session where messages will be displayed based on regular expressions"""
        self.is_regex = True

    def stop_regex(self):
        """Stop the regex session"""
        self.is_regex = False

    @contextmanager
    def regex(self):
        """Context managed regex session.

        Yields:
            CLI: Yields the current CLI instance with a regex session initialized
        """
        if self.is_regex:
            # if already regex, do nothing
            yield self
        else:
            self.start_regex()
            try:
                yield self
            finally:
                self.stop_regex()

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

        self.spinner.text = msg

    def prompt(self, msg: str) -> str:
        """Displays a prompt to the user and waits for an answer

        Args:
            msg (str): message to use for the prompt

        Returns:
            str: user input
        """
        return input(msg)

    def hidden_prompt(self, msg: str) -> str:
        """Displays a prompt to the user and waits for an aswer. User input is not displayed

        Args:
            msg (str): message to use for the prompt

        Returns:
            str: user input
        """
        return getpass(msg)

    def print_highlight(self, msg: str = ""):
        """Display a highlighted message

        Args:
            msg (str): message to print
        """
        msg = typer.style(msg, fg=typer.colors.GREEN)
        self._print(msg)

    def print_yaml(self, msg: str):
        """Display a yaml object on the command line

        Args:
            msg (str): message to display
        """
        self.print()
        self.print("=" * 20)
        self.print(msg)
        self.print("=" * 20)
