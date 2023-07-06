import time
from unittest.mock import ANY
from medperf.tests.mocks import MockResponse
from medperf.comms.auth.auth0 import Auth0

import pytest

PATCH_AUTH = "medperf.comms.auth.auth0.{}"


@pytest.fixture
def setup(mocker):
    mocker.patch(PATCH_AUTH.format("requests.post"), return_value=MockResponse({}, 200))


def test_logout_removes_credentials(mocker, setup):
    # Arrange
    creds = {"refresh_token": ""}
    mocker.patch(PATCH_AUTH.format("read_credentials"), return_value=creds)
    spy = mocker.patch(PATCH_AUTH.format("delete_credentials"))

    # Act
    Auth0().logout()

    # Assert
    spy.assert_called_once()


def test_token_is_not_refreshed_if_not_expired(mocker):
    # Arrange
    creds = {
        "refresh_token": "",
        "access_token": "",
        "token_expires_in": 900,
        "token_issued_at": time.time(),
    }
    mocker.patch(PATCH_AUTH.format("read_credentials"), return_value=creds)
    spy = mocker.patch(PATCH_AUTH.format("Auth0._Auth0__refresh_access_token"))

    # Act
    Auth0().access_token

    # Assert
    spy.assert_not_called()


def test_refresh_token_sets_new_tokens(mocker):
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
    Auth0()._Auth0__refresh_access_token("")

    # Assert
    spy.assert_called_once_with(
        access_token, refresh_token, id_token_payload, expires_in, ANY
    )
