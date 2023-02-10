from abc import ABC, abstractmethod


class BaseSource(ABC):
    @abstractmethod
    def __init__(self):
        """Initialize"""

    @abstractmethod
    def authenticate(self):
        """Authenticates with the source server, if needed."""

    @abstractmethod
    def download(self):
        """Downloads the requested resource to the specified location"""
