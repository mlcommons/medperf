import time
from medperf.exceptions import CommunicationError
import requests
import medperf.config as config
from medperf.utils import (
    set_credentials,
    read_credentials,
    delete_credentials,
    log_response_error,
)


class Auth:
    def __init__(self, domain, client_id, database, audience):
        self.domain = domain
        self.client_id = client_id
        self.database = database
        self.audience = audience

    def signup(self, email, password):
        url = f"https://{self.domain}/dbconnections/signup"
        headers = {"content-type": "application/json"}
        body = {
            "email": email,
            "password": password,
            "client_id": self.client_id,
            "connection": self.database,
        }
        res = requests.post(url=url, headers=headers, json=body)

        if res.status_code != 200:
            self.__raise_errors(res, "Signup")

    def change_password(self, email):
        url = f"https://{self.domain}/dbconnections/change_password"
        headers = {"content-type": "application/json"}
        body = {
            "client_id": self.client_id,
            "email": email,
            "connection": self.database,
        }
        res = requests.post(url=url, headers=headers, json=body)

        if res.status_code != 200:
            self.__raise_errors(res, "Password change")

    def login(self):
        device_code_response = self.__request_device_code()

        device_code = device_code_response["device_code"]
        user_code = device_code_response["user_code"]
        verification_uri_complete = device_code_response["verification_uri_complete"]
        interval = device_code_response["interval"]

        config.ui.print(
            "Please go to the following link to complete your login request:\n"
            f"\t{verification_uri_complete}\n\n"
            "Make sure that you will be presented with the following code:\n"
            f"\t{user_code}\n\n"
        )
        token_response, issued_at = self.__get_device_auth_token(device_code, interval)
        access_token = token_response["access_token"]
        refresh_token = token_response["refresh_token"]
        expires_in = token_response["expires_in"]

        set_credentials(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "issued_at": issued_at,
            }
        )

    def __request_device_code(self):
        url = f"https://{self.domain}/oauth/device/code"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = {
            "client_id": self.client_id,
            "audience": self.audience,
            "scope": "offline_access",  # to get a refresh token
        }
        res = requests.post(url=url, headers=headers, data=body)

        if res.status_code != 200:
            self.__raise_errors(res, "Login")

        return res.json()

    def __get_device_auth_token(self, device_code, polling_interval):
        url = f"https://{self.domain}/oauth/token"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": self.client_id,
        }

        while True:
            time.sleep(polling_interval)
            issued_at = time.time()
            res = requests.post(url=url, headers=headers, data=body)
            if res.status_code != 200:
                try:
                    json_res = res.json()
                except requests.exceptions.JSONDecodeError:
                    json_res = {}
                error = json_res.get("error", None)
                if error not in ["slow_down", "authorization_pending"]:
                    self.__raise_errors(res, "Login")
                continue
            return res.json(), issued_at

    def logout(self):
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
        creds = read_credentials()
        access_token = creds["access_token"]
        refresh_token = creds["refresh_token"]
        expires_in = creds["expires_in"]
        issued_at = creds["issued_at"]
        if time.time() > issued_at + expires_in - config.token_expiration_leeway:
            access_token = self.__refresh_access_token(refresh_token)
        return access_token

    def __refresh_access_token(self, refresh_token):
        url = f"https://{self.domain}/oauth/token"
        headers = {"content-type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": refresh_token,
        }
        issued_at = time.time()
        res = requests.post(url=url, headers=headers, data=body)

        if res.status_code != 200:
            self.__raise_errors(res, "Token refresh")

        json_res = res.json()

        access_token = json_res["access_token"]
        refresh_token = json_res["refresh_token"]
        expires_in = json_res["expires_in"]
        set_credentials(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in,
                "issued_at": issued_at,
            }
        )

        return access_token

    def __raise_errors(self, res, action):
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
