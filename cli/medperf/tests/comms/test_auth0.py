import time
from unittest.mock import ANY

from medperf.config_management import Auth0Settings
from medperf.tests.mocks import MockResponse
from medperf.comms.auth.auth0 import Auth0
from medperf import settings
from medperf.exceptions import AuthenticationError
import sqlite3
import pytest


PATCH_AUTH = "medperf.comms.auth.auth0.{}"

test_auth_config = Auth0Settings(
    domain=settings.auth_domain,
    jwks_url=settings.auth_jwks_url,
    idtoken_issuer=settings.auth_idtoken_issuer,
    client_id=settings.auth_client_id,
    audience=settings.auth_audience,
    jwks_cache_ttl=settings.auth_jwks_cache_ttl,
    tokens_db=settings.tokens_db,
    token_expiration_leeway=settings.token_expiration_leeway,
    token_absolute_expiry=settings.token_absolute_expiry,
    refresh_token_expiration_leeway=settings.refresh_token_expiration_leeway,
)

@pytest.fixture
def setup(mocker):
    db = mocker.create_autospec(sqlite3.Connection)
    mocker.patch(PATCH_AUTH.format("sqlite3.connect"), return_value=db)
    mocker.patch(PATCH_AUTH.format("requests.post"), return_value=MockResponse({}, 200))


def test_logout_removes_credentials(mocker, setup):
    # Arrange
    creds = {"refresh_token": ""}
    mocker.patch(PATCH_AUTH.format("read_credentials"), return_value=creds)
    spy = mocker.patch(PATCH_AUTH.format("delete_credentials"))

    # Act
    Auth0(test_auth_config).logout()

    # Assert
    spy.assert_called_once()


def test_token_is_not_refreshed_if_not_expired(mocker, setup):
    # Arrange
    creds = {
        "refresh_token": "",
        "access_token": "",
        "token_expires_in": 900,
        "token_issued_at": time.time(),
        "logged_in_at": time.time(),
    }
    mocker.patch(PATCH_AUTH.format("read_credentials"), return_value=creds)
    spy = mocker.patch(PATCH_AUTH.format("Auth0._Auth0__refresh_access_token"))

    # Act
    Auth0(test_auth_config).access_token

    # Assert
    spy.assert_not_called()


def test_token_is_refreshed_if_expired(mocker, setup):
    # Arrange
    expiration_time = 900
    mocked_issued_at = time.time() - expiration_time
    creds = {
        "refresh_token": "",
        "access_token": "",
        "token_expires_in": expiration_time,
        "token_issued_at": mocked_issued_at,
        "logged_in_at": time.time(),
    }
    mocker.patch(PATCH_AUTH.format("read_credentials"), return_value=creds)
    spy = mocker.patch(PATCH_AUTH.format("Auth0._Auth0__refresh_access_token"))

    # Act
    _ = Auth0(test_auth_config).access_token

    # Assert
    spy.assert_called_once()


def test_logs_out_if_session_reaches_token_absolute_expiration_time(mocker, setup):
    # Arrange
    expiration_time = 900
    absolute_expiration_time = settings.token_absolute_expiry
    mocked_logged_in_at = time.time() - absolute_expiration_time
    mocked_issued_at = time.time() - expiration_time
    creds = {
        "refresh_token": "",
        "access_token": "",
        "token_expires_in": expiration_time,
        "token_issued_at": mocked_issued_at,
        "logged_in_at": mocked_logged_in_at,
    }
    mocker.patch(PATCH_AUTH.format("read_credentials"), return_value=creds)
    spy = mocker.patch(PATCH_AUTH.format("Auth0.logout"))

    # Act
    with pytest.raises(AuthenticationError):
        _ = Auth0(test_auth_config).access_token

    # Assert
    spy.assert_called_once()


def test_refresh_token_sets_new_tokens(mocker, setup):
    # Arrange
    access_token = "access_token"
    refresh_token = "refresh_token"
    expires_in = "expires_in"
    id_token = "id_token"
    id_token_payload = "id_token_payload"

    res = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": expires_in,
        "id_token": id_token,
    }
    mocker.patch(
        PATCH_AUTH.format("requests.post"), return_value=MockResponse(res, 200)
    )
    mocker.patch(PATCH_AUTH.format("verify_token"), return_value=id_token_payload)
    spy = mocker.patch(PATCH_AUTH.format("set_credentials"))

    # Act
    Auth0(test_auth_config)._Auth0__refresh_access_token("")

    # Assert
    spy.assert_called_once_with(
        access_token, refresh_token, id_token_payload, ANY, expires_in
    )
