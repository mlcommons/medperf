import requests
import pytest

from medperf.web_ui.auth import AUTH_COOKIE_NAME
from medperf.web_ui.common import templates
from medperf.web_ui.tests import config as tests_config

BASE_URL = tests_config.BASE_URL
PATCH_ROUTE = "medperf.web_ui.medperf_login.{}"


def _post(sec_token, path, data=None):
    return requests.post(
        BASE_URL.format(path), data=data, cookies={AUTH_COOKIE_NAME: sec_token}
    )


@pytest.fixture(autouse=True)
def _restore_logged_in_global():
    # login()/logout() flip this Jinja *environment* global (not a
    # per-request context var), so it persists across every other test in
    # the run unless explicitly restored.
    original = templates.env.globals.get("logged_in")
    yield
    if original is None:
        templates.env.globals.pop("logged_in", None)
    else:
        templates.env.globals["logged_in"] = original


def test_logout_requires_auth():
    resp = requests.post(BASE_URL.format("/logout"))
    assert resp.status_code == 401


def test_logout_succeed(sec_token, mocker, ui, auth):
    mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    ui.end_task = mocker.Mock()
    ui.clear_notifications = mocker.Mock()
    auth.logout = mocker.Mock()

    resp = _post(sec_token, "/logout")

    assert resp.status_code == 200
    assert resp.json() == {"status": "success", "error": ""}

    auth.logout.assert_called_once()
    ui.clear_notifications.assert_called_once()
    ui.end_task.assert_called_once()
    assert templates.env.globals["logged_in"] is False


def test_logout_fails(sec_token, mocker, ui, auth):
    error_msg = "Logout test failed"
    mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    ui.end_task = mocker.Mock()
    auth.logout = mocker.Mock(side_effect=Exception(error_msg))

    resp = _post(sec_token, "/logout")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "failed"
    assert error_msg in body["error"]

    ui.end_task.assert_called_once()
