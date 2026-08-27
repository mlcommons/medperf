import requests

import medperf.config as config
from medperf.web_ui.auth import AUTH_COOKIE_NAME
from medperf.web_ui.tests import config as tests_config

BASE_URL = tests_config.BASE_URL


def _get(sec_token, path, **params):
    return requests.get(
        BASE_URL.format(path), params=params, cookies={AUTH_COOKIE_NAME: sec_token}
    )


def _post(sec_token, path, data):
    return requests.post(
        BASE_URL.format(path), data=data, cookies={AUTH_COOKIE_NAME: sec_token}
    )


def test_running_tasks_requires_auth():
    resp = requests.get(BASE_URL.format("/api/running_tasks"))
    assert resp.status_code == 401


def test_running_tasks_empty(sec_token, mocker):
    mocker.patch.object(config, "running_containers", {})

    resp = _get(sec_token, "/api/running_tasks")

    assert resp.status_code == 200
    assert resp.json() == {"tasks": []}


def test_running_tasks_lists_names(sec_token, mocker):
    mocker.patch.object(
        config, "running_containers", {"start_aggregator": object(), "train": object()}
    )

    resp = _get(sec_token, "/api/running_tasks")

    assert resp.status_code == 200
    assert sorted(resp.json()["tasks"]) == ["start_aggregator", "train"]


def test_stop_task_requires_auth():
    resp = requests.post(BASE_URL.format("/api/stop_task"), data={"task_name": "train"})
    assert resp.status_code == 401


def test_stop_task_not_found(sec_token, mocker):
    mocker.patch.object(config, "running_containers", {})

    resp = _post(sec_token, "/api/stop_task", {"task_name": "train"})

    assert resp.status_code == 404


def test_stop_task_succeed(sec_token, mocker):
    wrapper = mocker.MagicMock()
    mocker.patch.object(config, "running_containers", {"train": wrapper})

    resp = _post(sec_token, "/api/stop_task", {"task_name": "train"})

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    wrapper.killpg.assert_called_once()


def test_stop_task_fails(sec_token, mocker):
    wrapper = mocker.MagicMock()
    wrapper.killpg.side_effect = Exception("boom")
    mocker.patch.object(config, "running_containers", {"train": wrapper})

    resp = _post(sec_token, "/api/stop_task", {"task_name": "train"})

    assert resp.status_code == 500


def test_browse_directory_requires_auth():
    resp = requests.post(
        BASE_URL.format("/api/browse"), data={"path": "/tmp", "with_files": "true"}
    )
    assert resp.status_code == 401


def test_browse_directory_lists_folders_and_files(sec_token, tmp_path):
    (tmp_path / "b_dir").mkdir()
    (tmp_path / "a_dir").mkdir()
    (tmp_path / "file.txt").write_text("data")

    resp = _post(
        sec_token, "/api/browse", {"path": str(tmp_path), "with_files": "true"}
    )

    assert resp.status_code == 200
    data = resp.json()
    names = [f["name"] for f in data["folders"]]
    assert names == ["a_dir", "b_dir", "file.txt"]
    assert data["have_parent"] is True


def test_browse_directory_excludes_files_when_not_requested(sec_token, tmp_path):
    (tmp_path / "dir1").mkdir()
    (tmp_path / "file.txt").write_text("data")

    resp = _post(
        sec_token, "/api/browse", {"path": str(tmp_path), "with_files": "false"}
    )

    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["folders"]]
    assert names == ["dir1"]


def test_browse_directory_not_found(sec_token, tmp_path):
    resp = _post(
        sec_token,
        "/api/browse",
        {"path": str(tmp_path / "does-not-exist"), "with_files": "false"},
    )

    assert resp.status_code == 404
