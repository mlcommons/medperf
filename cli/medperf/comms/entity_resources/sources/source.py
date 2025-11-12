from abc import ABC, abstractmethod


class BaseSource(ABC):
    @classmethod
    @abstractmethod
    def validate_resource(cls, value: str):
        """Checks if an input resource can be downloaded by this class"""

    @abstractmethod
    def __init__(self):
        """Initialize"""

    @abstractmethod
    def authenticate(self):
        """Authenticates with the source server, if needed."""

    @abstractmethod
    def download(self, resource_identifier: str, output_path: str):
        """Downloads the requested resource to the specified location
        Args:
            resource_identifier (str): The identifier that is used to download
            the resource (e.g. URL, asset ID, ...) It is the parsed output
            by `validate_resource`
            output_path (str): The path to download the resource to
        """
