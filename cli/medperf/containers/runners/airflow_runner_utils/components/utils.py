from typing import Union
import requests
from http import HTTPStatus
from pydantic import SecretStr
import secrets


def validate_port(port: Union[int, str]) -> str:
    try:
        is_valid_port = 1 <= int(port) <= 65535
    except ValueError:
        is_valid_port = False

    if not is_valid_port:
        raise ValueError(f"Port value sent ({port}) is not a valid port!")

    return str(port)


def run_healthcheck(healthcheck_url: str) -> bool:
    try:
        response = requests.get(healthcheck_url)
        return response.status_code == HTTPStatus.OK
    except requests.exceptions.RequestException:
        return False


def generate_random_password(nbytes: int = 16) -> SecretStr:
    return SecretStr(secrets.token_urlsafe(nbytes))
