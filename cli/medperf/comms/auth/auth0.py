import time
import logging
import threading
import sqlite3
from medperf.comms.auth.interface import Auth
from medperf.comms.auth.token_verifier import verify_token
from medperf.exceptions import CommunicationError, AuthenticationError
import requests
import medperf.config as config
from medperf.utils import log_response_error
from medperf.account_management import (
    set_credentials,
    read_credentials,
    delete_credentials,
)


class Auth0(Auth):
    def __init__(self):
        self.domain = config.auth_domain
        self.client_id = config.auth_client_id
        self.audience = config.auth_audience
        self._lock = threading.Lock()

    def login(self, email):
        """Retrieves and stores an access token/refresh token pair from the auth0
        backend using the device authorization flow.

        Args:
            email (str): user email. This will be used to validate that the received
                         id_token contains the same email address.

        """
        device_code_response = self.__request_device_code()

        device_code = device_code_response["device_code"]
        user_code = device_code_response["user_code"]
        verification_uri_complete = device_code_response["verification_uri_complete"]
        interval = device_code_response["interval"]

        config.ui.print(
            "\nPlease go to the following link to complete your login request:\n"
            f"\t{verification_uri_complete}\n\n"
            "Make sure that you will be presented with the following code:\n"
            f"\t{user_code}\n\n"
        )
        config.ui.print_warning(
            "Keep this terminal open until you complete your login request. "
            "The command will exit on its own once you complete the request. "
            "If you wish to stop the login request anyway, press Ctrl+C."
        )
        token_response, token_issued_at = self.__get_device_access_token(
            device_code, interval
        )
        access_token = token_response["access_token"]
        id_token = token_response["id_token"]
        refresh_token = token_response["refresh_token"]
        token_expires_in = token_response["expires_in"]

        id_token_payload = verify_token(id_token)
        self.__check_token_email(id_token_payload, email)

        set_credentials(
            access_token,
            refresh_token,
            id_token_payload,
            token_issued_at,
            token_expires_in,
            login_event=True,
        )

    def __request_device_code(self):
        """Get a device code from the auth0 backend to be used for the authorization process"""
        url = f"https://{self.domain}/oauth/device/code"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = {
            "client_id": self.client_id,
            "audience": self.audience,
            "scope": "offline_access openid email",
        }
        res = requests.post(url=url, headers=headers, data=body)

        if res.status_code != 200:
            self.__raise_errors(res, "Login")

        return res.json()

    def __get_device_access_token(self, device_code, polling_interval):
        """Get the access token from the auth0 backend associated with
        the device code requested before. This function will keep polling
        the access token until the user completes the browser flow part
        of the authorization process.

        Args:
            device_code (str): A temporary device code requested by `__request_device_code`
            polling_interval (float): number of seconds to wait between each two polling requests

        Returns:
            json_res (dict): the response of the successful request, containg the access/refresh tokens pair
            token_issued_at (float): the timestamp when the access token was issued
        """
        url = f"https://{self.domain}/oauth/token"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": self.client_id,
        }

        while True:
            time.sleep(polling_interval)
            token_issued_at = time.time()
            res = requests.post(url=url, headers=headers, data=body)
            if res.status_code == 200:
                json_res = res.json()
                return json_res, token_issued_at

            try:
                json_res = res.json()
            except requests.exceptions.JSONDecodeError:
                json_res = {}
            error = json_res.get("error", None)
            if error not in ["slow_down", "authorization_pending"]:
                self.__raise_errors(res, "Login")

    def __check_token_email(self, id_token_payload, email):
        """Checks if the email provided by the user in the terminal matches the
        email found in the recieved id token."""
        email_in_token = id_token_payload["email"]
        if email.lower() != email_in_token:
            raise CommunicationError(
                "The email provided in the terminal does not match the one provided during login"
            )

    def logout(self):
        """Logs out the user by revoking their refresh token and deleting the
        stored tokens."""

        creds = read_credentials()
        refresh_token = creds["refresh_token"]

        url = f"https://{self.domain}/oauth/revoke"
        headers = {"content-type": "application/json"}
        body = {
            "client_id": self.client_id,
            "token": refresh_token,
        }
        res = requests.post(url=url, headers=headers, json=body)

        if res.status_code != 200:
            self.__raise_errors(res, "Logout")

        delete_credentials()

    @property
    def access_token(self):
        """Thread and process-safe access token retrieval"""
        # In case of multiple threads are using the same connection object,
        # keep the thread lock, otherwise the database will throw
        # errors of starting a transaction within a transaction.
        # In case of each thread is using a different connection object,
        # keep the thread lock to avoid the OperationalError when
        # multiple threads want to access the database.
        with self._lock:
            # TODO: This is temporary. Use a cleaner solution.
            db = sqlite3.connect(config.tokens_db, isolation_level=None, timeout=60)
            try:
                db.execute("BEGIN EXCLUSIVE TRANSACTION")
            except sqlite3.OperationalError:
                msg = "Another process is using the database. Try again later"
                raise CommunicationError(msg)
            token = self._access_token
            # Sqlite will automatically execute COMMIT and close the connection
            # if an exception is raised during the retrieval of the access token.
            db.execute("COMMIT")
            db.close()

            return token

    @property
    def _access_token(self):
        """Reads and returns an access token of the currently logged
        in user to be used for authorizing requests to the MedPerf server.
        Refresh the token if necessary.

        Returns:
            access_token (str): the access token
        """

        creds = read_credentials()
        access_token = creds["access_token"]
        refresh_token = creds["refresh_token"]
        token_expires_in = creds["token_expires_in"]
        token_issued_at = creds["token_issued_at"]
        logged_in_at = creds["logged_in_at"]

        # token_issued_at and expires_in are for the access token
        sliding_expiration_time = (
            token_issued_at + token_expires_in - config.token_expiration_leeway
        )
        absolute_expiration_time = (
            logged_in_at
            + config.token_absolute_expiry
            - config.refresh_token_expiration_leeway
        )
        current_time = time.time()

        if current_time < sliding_expiration_time:
            # Access token not expired. No need to refresh.
            return access_token

        # So we need to refresh.
        if current_time > absolute_expiration_time:
            # Expired refresh token. Force logout and ask the user to re-authenticate
            logging.debug(
                f"Refresh token expired: {absolute_expiration_time=} <> {current_time=}"
            )
            self.logout()
            raise AuthenticationError("Token expired. Please re-authenticate")

        # Expired access token and not expired refresh token. Refresh.
        access_token = self.__refresh_access_token(refresh_token)

        return access_token

    def __refresh_access_token(self, refresh_token):
        """Retrieve and store a new access token using a refresh token.
        A new refresh token will also be retrieved and stored.

        Args:
            refresh_token (str): the refresh token
        Returns:
            access_token (str): the new access token
        """

        url = f"https://{self.domain}/oauth/token"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": refresh_token,
        }
        token_issued_at = time.time()
        logging.debug("Refreshing access token.")
        res = requests.post(url=url, headers=headers, data=body)

        if res.status_code != 200:
            self.__raise_errors(res, "Token refresh")

        json_res = res.json()

        access_token = json_res["access_token"]
        id_token = json_res["id_token"]
        refresh_token = json_res["refresh_token"]
        token_expires_in = json_res["expires_in"]

        id_token_payload = verify_token(id_token)
        set_credentials(
            access_token,
            refresh_token,
            id_token_payload,
            token_issued_at,
            token_expires_in,
        )

        return access_token

    def __raise_errors(self, res, action):
        """log the failed request's response and raise errors.

        Args:
            res (requests.Response): the response of a failed request
            action (str): a string for more informative error display
            to the user.
        """

        log_response_error(res)
        if res.status_code == 429:
            raise CommunicationError("Too many requests. Try again later.")

        try:
            json_res = res.json()
        except requests.exceptions.JSONDecodeError:
            json_res = {}

        description = json_res.get("error_description", "")
        msg = f"{action} failed."
        if description:
            msg += f" {description}"
        raise CommunicationError(msg)
