from .cli import CLI
from .ui import UI


class UIFactory:
    @staticmethod
    def create_ui(name: str) -> UI:
        name = name.lower()
        if name == "cli":
            return CLI()
        else:
            raise NameError(f"{name}: the indicated UI interface doesn't exist")
