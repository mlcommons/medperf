from medperf import config
import synapseclient
from synapseclient.core.exceptions import SynapseError
from medperf.exceptions import CommunicationAuthenticationError


class SynapseLogin:
    # TODO: decide
    @staticmethod
    def run(username: str = None, password: str = None):
        """Login to the Synapse server. Must be done only once.
        """
        username = username if username else config.ui.prompt("username: ")
        password = password if password else config.ui.hidden_prompt("password: ")

        syn = synapseclient.Synapse()
        try:
            syn.login(username, password, rememberMe=True)
        except SynapseError:
            raise CommunicationAuthenticationError("Invalid Synapse credentials")

    def run_disabled_for_now(username: str = None, password: str = None):
        """Login to the Synapse server with access token. Must be done only once.
        """
        # TODO: if we go with this option, handle errors
        # move function out and move imports out

        def get_access_token(username, password):
            # https://rest-docs.synapse.org/rest/POST/login2.html
            import requests

            url = "https://repo-prod.prod.sagebase.org/auth/v1/login2"
            body = {"username": username, "password": password}
            res = requests.post(url, json=body)
            return res.json()["accessToken"]

        username = username if username else config.ui.prompt("username: ")
        password = password if password else config.ui.hidden_prompt("password: ")
        access_token = get_access_token(username, password)

        syn = synapseclient.Synapse()
        syn.login(authToken=access_token, rememberMe=True)
