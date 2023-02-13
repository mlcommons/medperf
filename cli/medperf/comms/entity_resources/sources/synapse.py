import synapseclient
from synapseclient.core.exceptions import SynapseError
from medperf.exceptions import (
    CommunicationRetrievalError,
    CommunicationAuthenticationError,
)
import os
import shutil
from .source import BaseSource
import re


class SynapseSource(BaseSource):
    @classmethod
    def validate_resource(cls, value):
        prefix = "synapse:"
        if not value.startswith(prefix):
            return

        prefix_len = len(prefix)
        value = value[prefix_len:]

        if re.match(r"syn\d+$", value):
            return value

    def __init__(self):
        self.client = synapseclient.Synapse()

    def authenticate(self):
        try:
            self.client.login(silent=True)
        except SynapseError as e:
            msg = "There was an attempt to download resources from the Synapse "
            msg += "platform, but couldn't find Synapse credentials: " + str(e)
            msg += "\nDid you run 'medperf synapse_login' before?"
            raise CommunicationAuthenticationError(msg)

    def download(self, resource_identifier: str, output_path: str):
        # we can specify target folder only. File name depends on how it was stored
        download_location = os.path.dirname(output_path)
        os.makedirs(download_location, exist_ok=True)
        try:
            resource_file = self.client.get(
                resource_identifier, downloadLocation=download_location
            )
        except SynapseError as e:
            raise CommunicationRetrievalError(str(e))

        resource_path = os.path.join(download_location, resource_file.name)
        # synapseclient may only throw a warning in some cases
        # (e.g. read permissions but no download permissions)
        if not os.path.exists(resource_path):
            raise CommunicationRetrievalError(
                "There was a problem retrieving a file from Synapse"
            )
        shutil.move(resource_path, output_path)
