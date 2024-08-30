import synapseclient
from synapseclient.core.exceptions import SynapseAuthenticationError
from medperf import settings
from medperf.exceptions import CommunicationAuthenticationError


class SynapseLogin:
    @classmethod
    def run(cls, token: str = None):
        """Login to the Synapse server. Must be done only once."""
        if not token:
            msg = (
                "Please provide your Synapse Personal Access Token (PAT). "
                "You can generate a new PAT at "
                "https://www.synapse.org/#!PersonalAccessTokens:0\n"
                "Synapse PAT: "
            )
            token = settings.ui.hidden_prompt(msg)
        cls.login_with_token(token)

    @classmethod
    def login_with_token(cls, access_token=None):
        """Login to the Synapse server. Must be done only once."""
        syn = synapseclient.Synapse()
        try:
            syn.login(authToken=access_token)
        except SynapseAuthenticationError as err:
            raise CommunicationAuthenticationError("Invalid Synapse credentials") from err
