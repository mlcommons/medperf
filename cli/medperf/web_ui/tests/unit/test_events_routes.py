import requests

from medperf.web_ui.auth import AUTH_COOKIE_NAME
from medperf.web_ui.tests import config as tests_config

BASE_URL = tests_config.BASE_URL


def _post(sec_token, path, data):
    return requests.post(
        BASE_URL.format(path), data=data, cookies={AUTH_COOKIE_NAME: sec_token}
    )


def _get(sec_token, path, **params):
    return requests.get(
        BASE_URL.format(path), params=params, cookies={AUTH_COOKIE_NAME: sec_token}
    )


def test_mark_read_requires_auth():
    resp = requests.post(
        BASE_URL.format("/notifications/mark_read"), data={"notification_id": "1"}
    )
    assert resp.status_code == 401


def test_mark_read_calls_ui(sec_token, ui, mocker):
    # read_notification isn't declared on the abstract UI base class the
    # `ui` fixture is autospec'd from (only concrete-subclass-only
    # methods), so it has to be attached explicitly before the mock will
    # accept calls to it.
    ui.read_notification = mocker.Mock()

    resp = _post(sec_token, "/notifications/mark_read", {"notification_id": "abc"})

    assert resp.status_code == 200
    ui.read_notification.assert_called_once_with("abc")


def test_delete_notification_calls_ui(sec_token, ui, mocker):
    ui.delete_notification = mocker.Mock()

    resp = _post(sec_token, "/notifications/delete", {"notification_id": "abc"})

    assert resp.status_code == 200
    ui.delete_notification.assert_called_once_with("abc")


def test_current_task_returns_task_id(sec_token, ui):
    ui.task_id = "abc-123"

    resp = _get(sec_token, "/current_task")

    assert resp.status_code == 200
    assert resp.json() == {"task_id": "abc-123"}


def test_current_task_requires_auth():
    resp = requests.get(BASE_URL.format("/current_task"))
    assert resp.status_code == 401


def test_acknowledge_event_calls_ui(sec_token, ui, mocker):
    ui.acknowledge_event = mocker.Mock()

    resp = _post(sec_token, "/events/acknowledge_event", {"event_id": "5"})

    assert resp.status_code == 200
    assert resp.json() == {"status": "success"}
    ui.acknowledge_event.assert_called_once_with(5)


def test_respond_to_prompt_calls_ui(sec_token, ui, mocker):
    ui.set_response = mocker.Mock()

    resp = _post(sec_token, "/events", {"is_approved": "true"})

    assert resp.status_code == 200
    ui.set_response.assert_called_once_with({"value": True})
