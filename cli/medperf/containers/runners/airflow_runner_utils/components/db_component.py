from .component import ComponentRunner
from abc import abstractmethod


class DatabaseComponent(ComponentRunner):

    @property
    @abstractmethod
    def connection_string(self):
        pass
