from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.settings_page import SettingsPage

import pytest
from unittest.mock import MagicMock

BASE_URL = tests_config.BASE_URL

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


class _MockConfig:
    active_profile_name = "local"

    def __iter__(self):
        return iter(["local", "server"])


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
    assert "View Profile" in page.get_text(page.VIEW_PROFILE)

    page.wait_for_presence_selector(page.EDIT_CONFIG_FORM)
    assert page.get_text(page.GPUS_LABEL) == "GPUs"
    assert page.get_text(page.PLATFORM_LABEL) == "Platform"
    assert page.get_text(page.CA_LABEL) == "Certificate Authority"
    assert page.get_text(page.FINGERPRINT_LABEL) == "Fingerprint"
    assert "Apply Changes" in page.get_text(page.APPLY_CHANGES)

    page.wait_for_presence_selector(page.CERT_SECTION_HEADING)
    assert page.get_text(page.CERT_SECTION_HEADING) == "Signing Certificate Settings"
    assert "No Certificate Found" in page.get_text(page.CERT_SETTINGS)
    page.wait_for_presence_selector(page.GET_CERTIFICATE)
    assert "Get User Certificate" in page.get_text(page.GET_CERTIFICATE)

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
    assert "Delete" in page.get_text(page.DELETE_CERTIFICATE)

    assert page.driver.find_elements(*page.GET_CERTIFICATE) == []


def test_settings_page_certificate_to_submit(page, patch_settings_ui_submit_cert):
    page.open(BASE_URL.format("/settings"))

    page.wait_for_presence_selector(page.CERTIFICATE_STATUS)
    assert page.get_text(page.CERTIFICATE_STATUS) == "to be uploaded"

    page.wait_for_presence_selector(page.SUBMIT_CERTIFICATE)
    assert "Submit Certificate" in page.get_text(page.SUBMIT_CERTIFICATE)
    page.wait_for_presence_selector(page.DELETE_CERTIFICATE)


def test_settings_page_certificate_invalid(page, patch_settings_ui_invalid_cert):
    page.open(BASE_URL.format("/settings"))

    page.wait_for_presence_selector(page.CERTIFICATE_STATUS)
    assert page.get_text(page.CERTIFICATE_STATUS) == "invalid"
    page.wait_for_presence_selector(page.DELETE_CERTIFICATE)
