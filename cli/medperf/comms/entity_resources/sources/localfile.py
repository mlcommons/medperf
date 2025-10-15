from .source import BaseSource
import os
import shutil


class LocalFileSource(BaseSource):

    @classmethod
    def validate_resource(cls, value: str):
        value_exists = os.path.exists(value)
        value_is_file = os.path.isfile(value)

        if value_exists and value_is_file:
            return value

    def __init__(self):
        pass

    def authenticate(self):
        pass

    def download(self, resource_identifier: str, output_path: str):
        """
        Simply makes a copy of the file at the desired output path.
        """
        shutil.copy2(resource_identifier, output_path)

    def read_content(self, resource_identifier: str) -> bytes:
        with open(resource_identifier, 'rb') as f:
            content = f.read()
        return content
