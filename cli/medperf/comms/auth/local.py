from medperf.comms.auth.interface import Auth
from medperf.exceptions import InvalidArgumentError
from medperf.account_management import (
    set_credentials,
    read_credentials,
    delete_credentials,
)
import json


class Local(Auth):
    def __init__(self, local_tokens_path):
        with open(local_tokens_path) as f:
            self.tokens = json.load(f)

    def login(self, email):
        """Retrieves and stores an access token from a local store json file.

        Args:
            email (str): user email.
        """

        try:
            access_token = self.tokens[email]
        except KeyError:
            raise InvalidArgumentError(
                "The provided email does not exist for testing. "
                "Make sure you activated the right profile."
            )
        refresh_token = "refresh token"
        id_token_payload = {"email": email}
        token_issued_at = 0
        token_expires_in = 10**10

        set_credentials(
            access_token,
            refresh_token,
            id_token_payload,
            token_issued_at,
            token_expires_in,
            login_event=True,
        )

    def logout(self):
        """Logs out the user by deleting the stored tokens."""
        delete_credentials()

    @property
    def access_token(self):
        """Reads and returns an access token of the currently logged
        in user to be used for authorizing requests to the MedPerf server.

        Returns:
            access_token (str): the access token
        """

        creds = read_credentials()
        access_token = creds["access_token"]
        return access_token
