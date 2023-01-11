from abc import ABC, abstractmethod
from contextlib import contextmanager


class UI(ABC):
    @abstractmethod
    def print(self, msg: str = ""):
        """Display a message to the interface. If on interactive session overrides
        previous message
        """

    @abstractmethod
    def print_error(self, msg: str):
        """Display an error message to the interface"""

    @abstractmethod
    def start_interactive(self):
        """Initialize an interactive session for animations or overriding messages.
        If the UI doesn't support this, the function can be left empty.
        """

    @abstractmethod
    def stop_interactive(self):
        """Terminate an interactive session.
        If the UI doesn't support this, the function can be left empty.
        """

    @abstractmethod
    @contextmanager
    def interactive(self):
        """Context managed interactive session. Expected to yield the same instance
        """

    @abstractmethod
    def text(self, msg: str):
        """Displays a messages that overwrites previous messages if they were created
        during an interactive session.
        If not supported or not on an interactive session, it is expected to fallback
        to the UI print function.

        Args:
            msg (str): message to display
        """

    @abstractmethod
    def prompt(msg: str) -> str:
        """Displays a prompt to the user and waits for an answer"""

    @abstractmethod
    def hidden_prompt(self, msg: str) -> str:
        """Displays a prompt to the user and waits for an aswer. User input is not displayed

        Args:
            msg (str): message to use for the prompt

        Returns:
            str: user input
        """

    @abstractmethod
    def print_highlight(self, msg: str = ""):
        """Display a message on the command line with green color

        Args:
            msg (str): message to print
        """
