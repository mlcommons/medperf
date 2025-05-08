from .cli import CLI
from .interface import UI
from .stdin import StdIn
from .web_ui import WebUI
from medperf.exceptions import InvalidArgumentError


class UIFactory:
    @staticmethod
    def create_ui(name: str) -> UI:
        if isinstance(name, CLI):
            return CLI()
        elif isinstance(name, WebUI):
            return WebUI()
        elif isinstance(name, StdIn):
            return StdIn()
        name = name.lower()
        if name == "cli":
            return CLI()
        elif name == "webui":
            return WebUI()
        elif name == "stdin":
            return StdIn()
        else:
            msg = f"{name}: the indicated UI interface doesn't exist"
            raise InvalidArgumentError(msg)
