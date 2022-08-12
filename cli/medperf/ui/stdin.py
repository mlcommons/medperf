from contextlib import contextmanager

from .interface import UI


class StdIn(UI):
    """
    Class for using sys.stdin/sys.stdout exclusively. Used mainly for automating
    execution with class-like objects. Using only basic IO methods ensures that
    piping from the command-line. Should not be used in normal execution, as
    hidden prompts and interactive prints will not work as expected.
    """

    def print(self, msg: str = ""):
        return print(msg)

    def print_error(self, msg: str):
        return self.print(msg)

    def start_interactive(self):
        pass

    def stop_interactive(self):
        pass

    @contextmanager
    def interactive(self):
        yield self

    @property
    def text(self):
        return ""

    @text.setter
    def text(self, msg: str = ""):
        return

    def prompt(self, msg: str) -> str:
        return input(msg)

    def hidden_prompt(self, msg: str) -> str:
        return self.prompt(msg)
