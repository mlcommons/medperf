from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.container.details_page import ContainerDetailsPage
from medperf.web_ui.tests.unit.helpers import (
    patch_medperf_session,
    stub_event_generator,
)

import pytest
from unittest.mock import ANY, MagicMock
from medperf.tests.mocks.model import TestModel
from medperf.tests.mocks.encrypted_key import TestEncryptedKey
from medperf.web_ui.app import web_app
import medperf.web_ui.events as events_module

BASE_URL = tests_config.BASE_URL

PATCH_ROUTE = "medperf.web_ui.containers.routes.{}"
PATCH_CUBE_GET = "medperf.entities.cube.Cube.get"
PATCH_MODEL_GET_BY_CONTAINER = "medperf.entities.model.Model.get_by_container"
PATCH_MODEL_GET_BMK_ASSOCS = "medperf.entities.model.Model.get_benchmarks_associations"
PATCH_GET_CONTAINER_KEYS = (
    "medperf.entities.encrypted_key.EncryptedKey.get_container_keys"
)

CONTAINER_ID = 10
CONTAINER_NAME = "test_container"
CONTAINER_OWNER = 1
MODEL_ID = 20


def _make_container_mock(**overrides):
    m = MagicMock()
    m.id = CONTAINER_ID
    m.name = CONTAINER_NAME
    m.owner = CONTAINER_OWNER
    m.is_encrypted.return_value = True
    # container_details_ui (the redirect target when not encrypted) branches
    # on is_model() to decide whether to call Model.get_by_container for
    # real; keep it False here so that unrelated tests don't need to mock
    # the model-resolution path too.
    m.is_model.return_value = False
    for key, val in overrides.items():
        setattr(m, key, val)
    return m


@pytest.fixture
def container_mock(mocker):
    m = _make_container_mock()
    mocker.patch(PATCH_CUBE_GET, return_value=m)
    yield m


@pytest.fixture
def access_mocks(mocker):
    # container_access_ui() renders the template with entity=<the Cube>, so
    # form hidden fields named "model_id" actually carry the container's id
    # (entity.id), not this wrapping Model's own id. This model is only used
    # to resolve get_benchmarks_associations(model_uid=...).
    model = TestModel(id=MODEL_ID, owner=CONTAINER_OWNER)
    mocker.patch(PATCH_MODEL_GET_BY_CONTAINER, return_value=model)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_GET_CONTAINER_KEYS, return_value=[])
    return model


@pytest.fixture
def page(driver):
    return ContainerDetailsPage(driver)


def _patch_user(mocker, user_id: int):
    patch_medperf_session(
        mocker,
        user_id,
        email="test@example.com",
        route_modules=("containers",),
        with_read_user_account=False,
    )


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification
    return (init, reset, notifs)


@pytest.fixture()
def patch_task_events(mocker, ui):
    # Grant/revoke/delete-keys all submit via the generic
    # form[id$='-form'] -> submitActionForm(WithForm) JS path (same one
    # dataset/model association-request forms use), which always polls
    # /current_task and opens a real /events SSE stream after submit. Both
    # are stubbed so the test doesn't hang on a real stream, and both are
    # expected to have been called exactly once (see
    # test_dataset_details_request_association_success for the established
    # pattern this mirrors).
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"
    return (spy_event_gen, spy_task_id)


@pytest.fixture()
def reset_auto_access():
    # start_auto_access spins up a real (daemon) background thread and
    # mutates the shared app.state.model_auto_give_access dict; reset it so
    # a leftover "running" state from this test can't leak into others that
    # load the access page for a different container.
    yield
    web_app.state.model_auto_give_access = {
        "running": False,
        "worker": None,
        "event": None,
        "benchmark": 0,
        "model": 0,
        "emails": "",
        "interval": 0,
    }


def test_container_access_redirect_non_owner(page, mocker, container_mock):
    _patch_user(mocker, CONTAINER_OWNER + 99)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    assert "You don't have access to this page" in page.driver.page_source


def test_container_access_redirect_when_not_encrypted(page, mocker, container_mock):
    container_mock.is_encrypted.return_value = False
    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    assert page.current_url == BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}")


def test_container_access_content_loaded_for_owner(
    page, mocker, container_mock, access_mocks
):
    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    assert page.get_text(page.ACCESS_HEADER) == f"Manage Access | {CONTAINER_NAME}"
    assert page.get_text(page.NO_KEYS_MSG) == "No users currently have access."
    assert page.find(page.DELETE_KEYS_BTN).get_attribute("disabled") == "true"


def test_container_access_shows_existing_keys(
    page, mocker, container_mock, access_mocks
):
    mocker.patch(
        PATCH_GET_CONTAINER_KEYS,
        return_value=[TestEncryptedKey(id=1, certificate=5)],
    )
    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    rows = page.find_elements(page.KEYS_TABLE_ROWS)
    assert len(rows) == 1
    assert page.find(page.revoke_btn(1)) is not None
    assert page.find(page.DELETE_KEYS_BTN).get_attribute("disabled") is None


def test_container_grant_access_succeed(
    page, mocker, ui, container_mock, access_mocks, patch_common, patch_task_events
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_grant = mocker.patch(PATCH_ROUTE.format("GrantAccess.run"))

    benchmark = mocker.MagicMock()
    benchmark.id = 5
    benchmark.name = "test_benchmark"
    mocker.patch("medperf.entities.benchmark.Benchmark.all", return_value=[benchmark])

    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.grant_access("test_benchmark", ["test@test.com"])
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to grant access to the email(s) added?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)
    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="container_grant_access")
    spy_grant.assert_called_once_with(
        benchmark_id=5, model_id=CONTAINER_ID, allowed_emails="test@test.com"
    )
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_container_grant_access_fails(
    page, mocker, ui, container_mock, access_mocks, patch_common, patch_task_events
):
    error_msg = "Grant access test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_grant = mocker.patch(
        PATCH_ROUTE.format("GrantAccess.run"), side_effect=Exception(error_msg)
    )

    benchmark = mocker.MagicMock()
    benchmark.id = 5
    benchmark.name = "test_benchmark"
    mocker.patch("medperf.entities.benchmark.Benchmark.all", return_value=[benchmark])

    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.grant_access("test_benchmark", ["test@test.com"])
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="container_grant_access")
    spy_grant.assert_called_once_with(
        benchmark_id=5, model_id=CONTAINER_ID, allowed_emails="test@test.com"
    )
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_container_revoke_access_succeed(
    page, mocker, ui, container_mock, access_mocks, patch_common, patch_task_events
):
    mocker.patch(
        PATCH_GET_CONTAINER_KEYS,
        return_value=[TestEncryptedKey(id=1, certificate=5)],
    )

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_revoke = mocker.patch(PATCH_ROUTE.format("RevokeUserAccess.run"))

    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.revoke_access(1)
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to revoke access for the selected user?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)
    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="container_revoke_key")
    spy_revoke.assert_called_once_with(1)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_container_revoke_access_fails(
    page, mocker, ui, container_mock, access_mocks, patch_common, patch_task_events
):
    error_msg = "Revoke access test failed"
    mocker.patch(
        PATCH_GET_CONTAINER_KEYS,
        return_value=[TestEncryptedKey(id=1, certificate=5)],
    )

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_revoke = mocker.patch(
        PATCH_ROUTE.format("RevokeUserAccess.run"), side_effect=Exception(error_msg)
    )

    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.revoke_access(1)
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="container_revoke_key")
    spy_revoke.assert_called_once_with(1)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_container_delete_keys_succeed(
    page, mocker, ui, container_mock, access_mocks, patch_common, patch_task_events
):
    mocker.patch(
        PATCH_GET_CONTAINER_KEYS,
        return_value=[TestEncryptedKey(id=1, certificate=5)],
    )

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_delete = mocker.patch(PATCH_ROUTE.format("DeleteKeys.run"))

    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.delete_keys()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT) == "Are you sure you want to delete all keys?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)
    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="container_delete_keys")
    spy_delete.assert_called_once_with(CONTAINER_ID)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_container_delete_keys_fails(
    page, mocker, ui, container_mock, access_mocks, patch_common, patch_task_events
):
    error_msg = "Delete keys test failed"
    mocker.patch(
        PATCH_GET_CONTAINER_KEYS,
        return_value=[TestEncryptedKey(id=1, certificate=5)],
    )

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_delete = mocker.patch(
        PATCH_ROUTE.format("DeleteKeys.run"), side_effect=Exception(error_msg)
    )

    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.delete_keys()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="container_delete_keys")
    spy_delete.assert_called_once_with(CONTAINER_ID)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_container_start_auto_access_succeed(
    page, mocker, container_mock, access_mocks, reset_auto_access
):
    # start_auto_access only fails if Thread creation itself raises, which
    # isn't realistically inducible via mocking, so only the succeed path
    # is meaningful to test here.
    mocker.patch(PATCH_ROUTE.format("GrantAccess.run"))

    benchmark = mocker.MagicMock()
    benchmark.id = 5
    benchmark.name = "test_benchmark"
    mocker.patch("medperf.entities.benchmark.Benchmark.all", return_value=[benchmark])

    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.start_auto_access("test_benchmark", ["test@test.com"])
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to start automatic grant access for the selected benchmark?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE) == "Successfully Started Auto Grant Access"
    )

    assert web_app.state.model_auto_give_access["running"] is True
    assert web_app.state.model_auto_give_access["model"] == CONTAINER_ID
    assert web_app.state.model_auto_give_access["benchmark"] == 5


def test_container_stop_auto_access_succeed(
    page, mocker, container_mock, access_mocks, reset_auto_access
):
    web_app.state.model_auto_give_access = {
        "running": True,
        "worker": mocker.MagicMock(),
        "event": mocker.MagicMock(),
        "benchmark": 5,
        "model": CONTAINER_ID,
        "emails": "test@test.com",
        "interval": 5,
    }

    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}/access"))

    page.wait_for_presence_selector(page.RUNNING_BADGE)
    assert page.get_text(page.RUNNING_BADGE) == "Running"

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.stop_auto_access()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to stop automatic grant access?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE) == "Successfully Stopped Auto Grant Access"
    )

    assert web_app.state.model_auto_give_access["running"] is False
