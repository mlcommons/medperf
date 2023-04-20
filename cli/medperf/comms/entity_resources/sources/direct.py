import requests
from medperf.exceptions import CommunicationRetrievalError
from medperf import config
from medperf.utils import log_response_error
from .source import BaseSource
import validators
import os


class DirectLinkSource(BaseSource):
    prefix = "direct:"

    @classmethod
    def validate_resource(cls, value: str):
        """This class expects a resource string of the form
        `direct:<URL>` or only a URL.
        Args:
            resource (str): the resource string

        Returns:
            (str|None): The URL if the pattern matches, else None
        """
        prefix = cls.prefix
        if value.startswith(prefix):
            prefix_len = len(prefix)
            value = value[prefix_len:]

        if validators.url(value):
            return value

    def __init__(self):
        pass

    def authenticate(self):
        pass

    def __download_once(self, resource_identifier: str, output_path: str):
        """Downloads a direct-download-link file by streaming its contents. source:
        https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
        """
        with requests.get(resource_identifier, stream=True) as res:
            if res.status_code != 200:
                log_response_error(res)
                msg = (
                    "There was a problem retrieving the specified file at "
                    + resource_identifier
                )
                raise CommunicationRetrievalError(msg)

            with open(output_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=config.ddl_stream_chunk_size):
                    # NOTE: if the response is chunk-encoded, this may not work
                    # check whether this is common.
                    f.write(chunk)

    def download(self, resource_identifier: str, output_path: str):
        """Downloads a direct-download-link file with multiple attempts. This is
        done due to facing transient network failure from some direct download
        link servers."""

        attempt = 0
        while attempt < config.ddl_max_redownload_attempts:
            try:
                self.__download_once(resource_identifier, output_path)
                return
            except CommunicationRetrievalError:
                if os.path.exists(output_path):
                    os.remove(output_path)
                attempt += 1

        raise CommunicationRetrievalError(f"Could not download {resource_identifier}")
