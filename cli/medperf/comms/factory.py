from .rest import REST
from .interface import Comms
from medperf.exceptions import InvalidArgumentError


class CommsFactory:
    @staticmethod
    def create_comms(name: str, host: str) -> Comms:
        if isinstance(name, str):
            name = name.lower()
            if name == "rest":
                return REST(host)
            else:
                msg = "the indicated communication interface doesn't exist"
                raise InvalidArgumentError(msg)
        return REST(host)
