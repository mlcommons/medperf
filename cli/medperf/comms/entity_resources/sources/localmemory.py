from .source import BaseSource
import io
from tempfile import SpooledTemporaryFile
from typing import Union

IN_MEMORY_TYPES = Union[SpooledTemporaryFile, io.BytesIO, io.StringIO]


class LocalMemorySource(BaseSource):

    @classmethod
    def validate_resource(cls, value: IN_MEMORY_TYPES):
        if isinstance(value, (SpooledTemporaryFile, io.BytesIO, io.StringIO)):
            return value

    def __init__(self):
        pass

    def authenticate(self):
        pass

    def download(self, resource_identifier: IN_MEMORY_TYPES, output_path: str):
        """
        Copies memory value to the given location
        """
        with open(output_path, 'w') as f:
            f.write(resource_identifier.read())

    def read_content(self, resource_identifier: IN_MEMORY_TYPES) -> bytes:
        content = resource_identifier.read()

        if isinstance(content, str):
            content = content.encode()

        return content
