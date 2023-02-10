import synapseclient
from medperf.exceptions import (
    CommunicationRetrievalError,
    CommunicationAuthenticationError,
)
import os


class SynapseSource:
    prefix = "synapse"

    def __init__(self):
        self.client = synapseclient.Synapse()

    def authenticate(self):
        try:
            self.client.login()
        except Exception as e:
            raise e
            msg = "?" + str(e)
            raise CommunicationAuthenticationError(msg)

    def download(self, resource_identifier: str, output_path: str):
        # TODO: downloadLocation expects a folder
        download_location = os.path.dirname(output_path)
        os.makedirs(download_location, exist_ok=True)
        try:
            self.client.get(resource_identifier, downloadLocation=download_location)
        except Exception as e:
            raise e
            msg = "?" + str(e)
            raise CommunicationRetrievalError(msg)
