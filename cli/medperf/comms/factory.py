from .rest import REST
from .comms import Comms
from medperf.config import config
from medperf.ui import UI
from medperf.utils import pretty_error


class CommsFactory:
    @staticmethod
    def create_comms(name: str, ui: UI) -> Comms:
        name = name.lower()
        if name == "rest":
            return REST(config["server"], ui)
        else:
            pretty_error("the indicated communication interface doesn't exist", ui)

