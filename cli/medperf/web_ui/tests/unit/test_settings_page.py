from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.settings_page import SettingsPage
from medperf.web_ui.tests.unit.helpers import stub_event_generator

import pytest
from unittest.mock import ANY, MagicMock
import medperf.web_ui.events as events_module

BASE_URL = tests_config.BASE_URL

PATCH_ROUTE = "medperf.web_ui.settings.{}"
PATCH_READ_CONFIG = "medperf.web_ui.settings.read_config"
PATCH_READ_USER_ACCOUNT = "medperf.web_ui.common.read_user_account"
PATCH_CA_ALL = "medperf.entities.ca.CA.all"
PATCH_CERT_STATUS = "medperf.web_ui.settings.current_user_certificate_status"
PATCH_GET_MEDPERF_USER_OBJECT = "medperf.web_ui.settings.get_medperf_user_object"
PATCH_GET_MEDPERF_USER_DATA = "medperf.web_ui.common.get_medperf_user_data"

CERT_STATUS_NO_LOCAL = {
    "no_certs_found": True,
    "should_be_submitted": False,
    "should_be_invalidated": False,
    "no_action_required": False,
}

CERT_STATUS_VALID = {
    "no_certs_found": False,
    "should_be_submitted": False,
    "should_be_invalidated": False,
    "no_action_required": True,
}

CERT_STATUS_SUBMIT = {
    "no_certs_found": False,
    "should_be_submitted": True,
    "should_be_invalidated": False,
    "no_action_required": False,
}

CERT_STATUS_INVALID = {
    "no_certs_found": False,
    "should_be_submitted": False,
    "should_be_invalidated": True,
    "no_action_required": False,
}

CC_OPERATOR_VALUES = {
    "project_id": "proj-id",
    "service_account_name": "sa-name",
    "bucket": "bucket-name",
    "vm_zone": "us-central1-a",
    "vm_name": "vm-name",
}


class _MockConfig:
    active_profile_name = "local"
    # Only used by the view_profile flow (config_p[profile]); a single
    # fixed dict is enough since no test asserts its exact contents.
    active_profile = {"gpus": "0", "platform": "auto"}

    def __iter__(self):
        return iter(["local", "server"])

    def __getitem__(self, key):
        return self.active_profile

    def activate(self, profile):
        self.active_profile_name = profile


def _patch_logged_in_settings_mocks(mocker, cert_status):
    mocker.patch(PATCH_READ_CONFIG, return_value=_MockConfig())
    mocker.patch(
        PATCH_READ_USER_ACCOUNT,
        return_value={"email": "test@example.com"},
    )
    mocker.patch(PATCH_CA_ALL, return_value=[])
    mocker.patch(PATCH_CERT_STATUS, return_value=cert_status)
    mock_user = MagicMock()
    mock_user.get_cc_config.return_value = {}
    mock_user.is_cc_configured.return_value = False
    mock_user.is_cc_initialized.return_value = True
    mocker.patch(PATCH_GET_MEDPERF_USER_OBJECT, return_value=mock_user)
    mocker.patch(
        PATCH_GET_MEDPERF_USER_DATA,
        return_value={"id": 1, "email": "test@example.com"},
    )


@pytest.fixture
def page(driver):
    return SettingsPage(driver)


@pytest.fixture
def patch_settings_ui(mocker):
    _patch_logged_in_settings_mocks(mocker, CERT_STATUS_NO_LOCAL)


@pytest.fixture
def patch_settings_ui_valid_cert(mocker):
    _patch_logged_in_settings_mocks(mocker, CERT_STATUS_VALID)


@pytest.fixture
def patch_settings_ui_submit_cert(mocker):
    _patch_logged_in_settings_mocks(mocker, CERT_STATUS_SUBMIT)


@pytest.fixture
def patch_settings_ui_invalid_cert(mocker):
    _patch_logged_in_settings_mocks(mocker, CERT_STATUS_INVALID)


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification
    return (init, reset, notifs)


@pytest.fixture()
def patch_task_events(mocker, ui):
    # The settings-action forms all submit via the generic
    # form[class='settings-action-form'] -> submitActionForm(WithForm) JS
    # path, which always polls /current_task and opens a real /events SSE
    # stream after submit, regardless of whether the specific route manages
    # a server-side task (edit_cc_operator doesn't; the certificate actions
    # do). Both need stubbing so the test doesn't hang on a real stream.
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"
    return (spy_event_gen, spy_task_id)


def test_settings_page_content(page, patch_settings_ui):
    page.open(BASE_URL.format("/settings"))

    page.wait_for_presence_selector(page.FORM)
    page.wait_for_presence_selector(page.PROFILE)
    page.wait_for_presence_selector(page.ACTIVATE)
    page.wait_for_presence_selector(page.VIEW_PROFILE)

    assert page.get_text(page.HEADER) == "Settings"
    assert page.get_text(page.PROFILE_SECTION_HEADING) == "Profile Settings"
    assert page.get_text(page.CURRENT_PROFILE) == "Local"
    assert page.get_text(page.PROFILE_LABEL) == "Select Profile"
    assert page.get_text(page.VIEW_PROFILE) == "View Profile"

    page.wait_for_presence_selector(page.EDIT_CONFIG_FORM)
    assert page.get_text(page.GPUS_LABEL) == "GPUs"
    assert page.get_text(page.PLATFORM_LABEL) == "Platform"
    assert page.get_text(page.CA_LABEL) == "Certificate Authority"
    assert page.get_text(page.FINGERPRINT_LABEL) == "Fingerprint"
    assert page.get_text(page.APPLY_CHANGES) == "Apply Changes"

    page.wait_for_presence_selector(page.CERT_SECTION_HEADING)
    assert page.get_text(page.CERT_SECTION_HEADING) == "Certificate Settings"
    assert "No Certificate Found" in page.get_text(page.CERT_SETTINGS)
    page.wait_for_presence_selector(page.GET_CERTIFICATE)
    assert page.get_text(page.GET_CERTIFICATE) == "Get User Certificate"

    page.wait_for_presence_selector(page.CC_OPERATOR_SECTION)
    assert "Confidential Computing Operator Settings" in page.get_text(
        page.CC_OPERATOR_SECTION
    )
    page.wait_for_presence_selector(page.CC_OPERATOR_FORM)
    page.wait_for_presence_selector(page.CC_CONFIGURE_TOGGLE)


def test_settings_page_not_logged_in(page, mocker):
    mocker.patch(PATCH_READ_CONFIG, return_value=_MockConfig())
    mocker.patch(PATCH_READ_USER_ACCOUNT, return_value=None)

    page.open(BASE_URL.format("/settings"))

    page.wait_for_presence_selector(page.FORM)
    assert page.get_text(page.CURRENT_PROFILE) == "Local"

    page.wait_for_presence_selector(page.CERT_SETTINGS)
    assert "Log in to view certificate settings" in page.get_text(page.CERT_SETTINGS)

    assert page.driver.find_elements(*page.CC_OPERATOR_SECTION) == []


def test_settings_page_certificate_valid(page, patch_settings_ui_valid_cert):
    page.open(BASE_URL.format("/settings"))

    page.wait_for_presence_selector(page.CERT_SETTINGS)
    assert "Certificate Exists" in page.get_text(page.CERT_SETTINGS)
    page.wait_for_presence_selector(page.CERTIFICATE_STATUS)
    assert page.get_text(page.CERTIFICATE_STATUS) == "valid"

    page.wait_for_presence_selector(page.DELETE_CERTIFICATE)
    assert page.get_text(page.DELETE_CERTIFICATE) == "Delete"

    assert page.driver.find_elements(*page.GET_CERTIFICATE) == []


def test_settings_page_certificate_to_submit(page, patch_settings_ui_submit_cert):
    page.open(BASE_URL.format("/settings"))

    page.wait_for_presence_selector(page.CERTIFICATE_STATUS)
    assert page.get_text(page.CERTIFICATE_STATUS) == "to be uploaded"

    page.wait_for_presence_selector(page.SUBMIT_CERTIFICATE)
    assert page.get_text(page.SUBMIT_CERTIFICATE) == "Submit Certificate"
    page.wait_for_presence_selector(page.DELETE_CERTIFICATE)


def test_settings_page_certificate_invalid(page, patch_settings_ui_invalid_cert):
    page.open(BASE_URL.format("/settings"))

    page.wait_for_presence_selector(page.CERTIFICATE_STATUS)
    assert page.get_text(page.CERTIFICATE_STATUS) == "invalid"
    page.wait_for_presence_selector(page.DELETE_CERTIFICATE)


def test_settings_activate_profile_succeed(page, mocker, patch_settings_ui):
    mocker.patch(PATCH_READ_CONFIG, return_value=_MockConfig())
    mocker.patch(PATCH_ROUTE.format("write_config"))
    mocker.patch(PATCH_ROUTE.format("initialize"))

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.activate_profile("Server")
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to activate this profile?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Profile Activated Successfully"


def test_settings_view_profile_succeed(page, mocker, patch_settings_ui):
    mocker.patch(PATCH_READ_CONFIG, return_value=_MockConfig())

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.view_profile()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to view this profile?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "View Profile"
    assert "local" in page.driver.page_source

    close_btn = popup_modal.find_element(
        "css selector", "#page-modal-footer .close-modal-btn"
    )
    page.ensure_element_ready(close_btn)
    close_btn.click()
    page.wait_for_invisibility_element(popup_modal)


def test_settings_edit_profile_succeed(
    page, mocker, ui, patch_common, patch_task_events, patch_settings_ui
):
    mocker.patch("medperf.web_ui.settings.config.gpus", "0")

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_set_args = mocker.patch(PATCH_ROUTE.format("set_profile_args"))
    mocker.patch(PATCH_ROUTE.format("initialize"))

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.edit_profile(gpus="1")
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to edit this profile?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE) == "Profile Settings Edited Successfully"
    )

    spy_set_args.assert_called_once()
    assert spy_set_args.call_args.args[0]["gpus"] == "1"


def test_settings_edit_profile_fails(
    page, mocker, ui, patch_common, patch_task_events, patch_settings_ui
):
    mocker.patch("medperf.web_ui.settings.config.gpus", "0")

    error_msg = "Edit profile test failed"
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_set_args = mocker.patch(
        PATCH_ROUTE.format("set_profile_args"), side_effect=Exception(error_msg)
    )

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.edit_profile(gpus="1")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Failed to Edit Profile Settings"
    assert error_msg in error_modal.text

    spy_set_args.assert_called_once()


def test_settings_get_certificate_succeed(
    page, mocker, ui, patch_common, patch_task_events, patch_settings_ui
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_get_cert = mocker.patch(PATCH_ROUTE.format("GetUserCertificate.run"))

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.get_client_certificate()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to get a new certificate?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Getting Client Certificate completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="get_client_certificate")
    spy_get_cert.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_settings_get_certificate_fails(
    page, mocker, ui, patch_common, patch_task_events, patch_settings_ui
):
    error_msg = "Get certificate test failed"
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_get_cert = mocker.patch(
        PATCH_ROUTE.format("GetUserCertificate.run"), side_effect=Exception(error_msg)
    )

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.get_client_certificate()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while getting client certificate"
    )
    assert error_msg in error_modal.text

    spy_init.assert_called_once_with(ANY, task_name="get_client_certificate")
    spy_get_cert.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_settings_submit_certificate_succeed(
    page, mocker, ui, patch_common, patch_task_events, patch_settings_ui_submit_cert
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_submit_cert = mocker.patch(PATCH_ROUTE.format("SubmitCertificate.run"))

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.submit_certificate()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to submit the certificate?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Submitting Client Certificate completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="submit_client_certificate")
    spy_submit_cert.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_settings_submit_certificate_fails(
    page, mocker, ui, patch_common, patch_task_events, patch_settings_ui_submit_cert
):
    error_msg = "Submit certificate test failed"
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_submit_cert = mocker.patch(
        PATCH_ROUTE.format("SubmitCertificate.run"), side_effect=Exception(error_msg)
    )

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.submit_certificate()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while submitting client certificate"
    )
    assert error_msg in error_modal.text

    spy_init.assert_called_once_with(ANY, task_name="submit_client_certificate")
    spy_submit_cert.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_settings_delete_certificate_succeed(
    page, mocker, ui, patch_common, patch_task_events, patch_settings_ui_submit_cert
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_delete_cert = mocker.patch(PATCH_ROUTE.format("DeleteCertificate.run"))

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.delete_certificate()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to delete the certificate?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Deleting Client Certificate completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="delete_client_certificate")
    spy_delete_cert.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_settings_delete_certificate_fails(
    page, mocker, ui, patch_common, patch_task_events, patch_settings_ui_submit_cert
):
    error_msg = "Delete certificate test failed"
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_delete_cert = mocker.patch(
        PATCH_ROUTE.format("DeleteCertificate.run"), side_effect=Exception(error_msg)
    )

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.delete_certificate()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while deleting client certificate"
    )
    assert error_msg in error_modal.text

    spy_init.assert_called_once_with(ANY, task_name="delete_client_certificate")
    spy_delete_cert.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_settings_edit_cc_operator_succeed(
    page, mocker, ui, patch_task_events, patch_settings_ui
):
    spy_event_gen, spy_task_id = patch_task_events
    spy_configure = mocker.patch(PATCH_ROUTE.format("SetupCCOperator.run"))

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.configure_cc_operator(CC_OPERATOR_VALUES)
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to edit CC operator configuration?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE) == "CC Configuration Edited Successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_configure.assert_called_once_with(CC_OPERATOR_VALUES)
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_settings_edit_cc_operator_fails(
    page, mocker, ui, patch_task_events, patch_settings_ui
):
    error_msg = "Edit CC operator test failed"
    spy_event_gen, spy_task_id = patch_task_events
    spy_configure = mocker.patch(
        PATCH_ROUTE.format("SetupCCOperator.run"), side_effect=Exception(error_msg)
    )

    page.open(BASE_URL.format("/settings"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.configure_cc_operator(CC_OPERATOR_VALUES)
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Failed to Edit CC Configuration"
    assert error_msg in error_modal.text

    spy_configure.assert_called_once_with(CC_OPERATOR_VALUES)
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()
