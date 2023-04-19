from medperf import config
import synapseclient
from synapseclient.core.exceptions import SynapseAuthenticationError
from medperf.exceptions import CommunicationAuthenticationError, InvalidArgumentError


class SynapseLogin:
    @classmethod
    def run(cls, username: str = None, password: str = None, token: str = None):
        """Login to the Synapse server. Must be done only once.
        """
        if not any([username, password, token]):
            msg = "How do you want to login?\n"
            msg += "[1] Personal Access Token\n"
            msg += "[2] Username and Password\n"
            msg += "Select an option (1 or 2): "
            method = config.ui.prompt(msg)
            if method == "1":
                cls.login_with_token()
            elif method == "2":
                cls.login_with_password()
            else:
                raise InvalidArgumentError("Invalid input. Select either number 1 or 2")
        else:
            if token:
                if any([username, password]):
                    raise InvalidArgumentError(
                        "Invalid input. Either an access token, or a username and password, should be given"
                    )
                cls.login_with_token(token)
            else:
                cls.login_with_password(username, password)

    @classmethod
    def login_with_password(cls, username: str = None, password: str = None):
        """Login to the Synapse server. Must be done only once.
        """
        username = username if username else config.ui.prompt("username: ")
        password = password if password else config.ui.hidden_prompt("password: ")

        syn = synapseclient.Synapse()
        try:
            syn.login(username, password, rememberMe=True)
        except SynapseAuthenticationError:
            raise CommunicationAuthenticationError("Invalid Synapse credentials")

    @classmethod
    def login_with_token(cls, access_token=None):
        """Login to the Synapse server. Must be done only once.
        """
        access_token = (
            access_token if access_token else config.ui.hidden_prompt("access token: ")
        )

        syn = synapseclient.Synapse()
        try:
            syn.login(authToken=access_token, rememberMe=True)
        except SynapseAuthenticationError:
            raise CommunicationAuthenticationError("Invalid Synapse credentials")
