import typer
from getpass import getpass
from yaspin import yaspin
from contextlib import contextmanager

from .interface import UI


class CLI(UI):
    def __init__(self):
        self.spinner = yaspin(color="green")
        self.is_interactive = False

    def print(self, msg: str = ""):
        """Display a message on the command line

        Args:
            msg (str): message to print
        """
        self.__print(msg)

    def print_error(self, msg: str):
        """Display an error message on the command line

        Args:
            msg (str): error message to display
        """
        msg = f"❌ {msg}"
        msg = typer.style(msg, fg=typer.colors.RED, bold=True)
        self.__print(msg)

    def __print(self, msg: str = ""):
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
        """Stop an interactive session
        """
        self.is_interactive = False
        self.spinner.stop()

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
        self.__print(msg)
