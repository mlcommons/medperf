from .rest import REST
from .comms import Comms
from medperf.config import config


class CommsFactory:
    @staticmethod
    def createComms(name: str) -> Comms:
        name = name.lower()
        if name == "rest":
            return REST(config["server"])
        else:
            raise NameError("the indicated communication interface doesn't exist")

