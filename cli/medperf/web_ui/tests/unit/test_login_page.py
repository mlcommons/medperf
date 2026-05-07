from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.login_page import LoginPage

import pytest
from unittest.mock import ANY
from email_validator import EmailNotValidError

import medperf.web_ui.events as events_module

from medperf.web_ui.tests.unit.helpers import stub_event_generator

BASE_URL = tests_config.BASE_URL
EMAIL = "test@test.com"
PATCH_ROUTE = "medperf.web_ui.medperf_login.{}"


def _confirm_modal_mentions_login(confirm_text: str) -> None:
    lowered = confirm_text.lower()
    assert "sign in" in lowered and "email" in lowered


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification

    return (init, reset, notifs)


@pytest.fixture
def page(driver):
    return LoginPage(driver)


def test_login_page_content(page, mocker):
    mocker.patch(PATCH_ROUTE.format("read_user_account"), return_value=None)

    page.open(BASE_URL.format("/medperf_login"))

    page.wait_for_presence_selector(page.FORM)
    page.wait_for_presence_selector(page.EMAIL)
    page.wait_for_presence_selector(page.LOGIN)

    assert page.get_text(page.HEADER) == "Welcome Back"
    email_label = page.get_text(page.EMAIL_LABEL).replace("\n", " ").strip()
    assert "Email Address" in email_label
    login_btn = page.get_text(page.LOGIN).replace("\n", " ").strip()
    assert "Sign In" in login_btn


def test_login_page_already_logged_in(page, mocker, patch_common, ui):
    test_email = "test_email@test.com"
    error_msg = f"You are already logged in as {test_email}."

    spy_init, spy_reset, spy_notifs = patch_common
    spy_read_acc = mocker.patch(
        PATCH_ROUTE.format("read_user_account"), return_value={"email": test_email}
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format("/medperf_login"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.login(EMAIL)
    page.wait_for_visibility_element(confirm_modal)

    _confirm_modal_mentions_login(page.get_text(page.CONFIRM_TEXT))

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Login Failed"
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_with(ANY, task_name="medperf_login")
    spy_event_gen.assert_called_once_with(ANY, False)

    assert spy_read_acc.call_count == 2
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_login_page_invalid_email(page, mocker, patch_common, ui):
    error_msg = "Email not valid"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_read_acc = mocker.patch(
        PATCH_ROUTE.format("read_user_account"), return_value=None
    )
    spy_validate_email = mocker.patch(
        PATCH_ROUTE.format("validate_email"), side_effect=EmailNotValidError(error_msg)
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format("/medperf_login"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.login(EMAIL)
    page.wait_for_visibility_element(confirm_modal)

    _confirm_modal_mentions_login(page.get_text(page.CONFIRM_TEXT))

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Login Failed"
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="medperf_login")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_validate_email.assert_called_once_with(EMAIL, check_deliverability=False)

    assert spy_read_acc.call_count == 2
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_login_page_success(page, mocker, patch_common, ui, auth):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_read_acc = mocker.patch(
        PATCH_ROUTE.format("read_user_account"), return_value=None
    )
    spy_validate_email = mocker.patch(PATCH_ROUTE.format("validate_email"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    auth.login = mocker.Mock()
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format("/medperf_login"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.login(EMAIL)
    page.wait_for_visibility_element(confirm_modal)

    _confirm_modal_mentions_login(page.get_text(page.CONFIRM_TEXT))

    current_url = page.current_url
    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Logged in successfully"

    page.wait_for_url_change(current_url)

    spy_init.assert_called_once_with(ANY, task_name="medperf_login")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_validate_email.assert_called_once_with(EMAIL, check_deliverability=False)

    assert spy_read_acc.call_count == 3
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    auth.login.assert_called_once_with(EMAIL)
    ui.end_task.assert_called_once()
