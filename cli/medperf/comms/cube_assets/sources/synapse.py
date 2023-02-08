import synapseclient
from medperf.exceptions import (
    CommunicationRetrievalError,
    CommunicationAuthenticationError,
)


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
        try:
            self.client.get(resource_identifier, downloadLocation=output_path)
        except Exception as e:
            raise e
            msg = "?" + str(e)
            raise CommunicationRetrievalError(msg)
