from .rest import REST
from .interface import Comms
from medperf.utils import pretty_error


class CommsFactory:
    @staticmethod
    def create_comms(name: str, host: str) -> Comms:
        name = name.lower()
        if name == "rest":
            return REST(host)
        else:
            pretty_error("the indicated communication interface doesn't exist")
