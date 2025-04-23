# from typing import List
from abc import ABC, abstractmethod


class Comms(ABC):
    @abstractmethod
    def __init__(self, source: str):
        """Create an instance of a communication object.

        Args:
            source (str): location of the communication source. Where messages are going to be sent.
            ui (UI): Implementation of the UI interface.
            token (str, Optional): authentication token to be used throughout communication. Defaults to None.
        """
