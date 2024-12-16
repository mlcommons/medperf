from typing import Union

from .interface import Comms
from medperf.exceptions import InvalidArgumentError


def create_comms(name: str, host: str, cert: Union[str, bool, None]) -> Comms:
    from .rest import REST

    name = name.lower()
    if name == "rest":
        return REST(host, cert)
    else:
        msg = "the indicated communication interface doesn't exist"
        raise InvalidArgumentError(msg)
