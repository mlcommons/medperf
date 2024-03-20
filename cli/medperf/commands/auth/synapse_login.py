from medperf import config
import synapseclient
from synapseclient.core.exceptions import SynapseAuthenticationError
from medperf.exceptions import CommunicationAuthenticationError, InvalidArgumentError


class SynapseLogin:
    @classmethod
    def run(cls, token: str = None):
        """Login to the Synapse server. Must be done only once."""
        if not token:
            msg = "Please provide your Synapse Personal Access Token (PAT). "
            msg += "You can generate a new PAT at https://www.synapse.org/#!PersonalAccessTokens:0\n"
            msg += "Synapse PAT: "
            token = config.ui.hidden_prompt(msg)
        cls.login_with_token(token)


    @classmethod
    def login_with_token(cls, access_token=None):
        """Login to the Synapse server. Must be done only once."""
        access_token = (
            access_token if access_token else config.ui.hidden_prompt("access token: ")
        )

        syn = synapseclient.Synapse()
        try:
            syn.login(authToken=access_token, rememberMe=True)
        except SynapseAuthenticationError:
            raise CommunicationAuthenticationError("Invalid Synapse credentials")
