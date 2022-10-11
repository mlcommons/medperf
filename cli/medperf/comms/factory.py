from .rest import REST
from .interface import Comms
from medperf.ui.interface import UI
from medperf.utils import pretty_error


class CommsFactory:
    @staticmethod
    def create_comms(name: str, ui: UI, host: str) -> Comms:
        name = name.lower()
        if name == "rest":
            return REST(host, ui)
        else:
            pretty_error("the indicated communication interface doesn't exist", ui)
