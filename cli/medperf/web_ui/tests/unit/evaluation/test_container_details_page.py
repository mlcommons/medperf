from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.container.details_page import ContainerDetailsPage

import datetime

import pytest
from unittest.mock import MagicMock

BASE_URL = tests_config.BASE_URL

PATCH_CUBE_GET = "medperf.entities.cube.Cube.get"
PATCH_GET_MEDPERF_USER_DATA_ROUTES = (
    "medperf.web_ui.containers.routes.get_medperf_user_data"
)
PATCH_GET_MEDPERF_USER_DATA_COMMON = "medperf.web_ui.common.get_medperf_user_data"
PATCH_READ_USER_ACCOUNT = "medperf.web_ui.common.read_user_account"

CONTAINER_ID = 10
CONTAINER_NAME = "test_container"
CONTAINER_OWNER = 1


def _make_container_mock(**overrides):
    m = MagicMock()
    m.id = CONTAINER_ID
    m.name = CONTAINER_NAME
    m.owner = CONTAINER_OWNER
    m.state = "OPERATION"
    m.is_valid = True
    m.created_at = datetime.datetime(2025, 10, 15, 12, 0, 0)
    m.modified_at = datetime.datetime(2025, 10, 17, 12, 0, 0)
    m.container_config = {"key1": "value1"}
    m.parameters_config = {"parameter": "value"}
    m.additional_files_tarball_url = None
    m.is_model.return_value = False
    m.is_encrypted.return_value = False
    for key, val in overrides.items():
        setattr(m, key, val)
    return m


@pytest.fixture
def container_mock(mocker):
    m = _make_container_mock()
    mocker.patch(PATCH_CUBE_GET, return_value=m)
    mocker.patch(PATCH_READ_USER_ACCOUNT, return_value={"email": "ui@test.local"})
    yield m


@pytest.fixture
def page(driver):
    return ContainerDetailsPage(driver, CONTAINER_NAME, "")


def _patch_user(mocker, user_id: int):
    data = {"id": user_id, "email": "test@example.com"}
    mocker.patch(PATCH_GET_MEDPERF_USER_DATA_COMMON, return_value=data)
    mocker.patch(PATCH_GET_MEDPERF_USER_DATA_ROUTES, return_value=data)


@pytest.mark.parametrize("user_id", [CONTAINER_OWNER, CONTAINER_OWNER + 1])
def test_container_details_common_content(page, mocker, container_mock, user_id):
    _patch_user(mocker, user_id)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    assert page.get_text(page.HEADER) == CONTAINER_NAME
    assert "Details" in page.get_text(page.DETAILS_HEADING)

    assert "Container ID" in page.get_text(page.CONTAINER_ID_LABEL)
    assert page.get_text(page.CONTAINER_ID_VALUE) == str(CONTAINER_ID)

    assert "Container Manifest" in page.get_text(page.MANIFEST_LABEL)
    assert "Click to display Container Configuration" in page.get_text(
        page.MANIFEST_YAML_BTN
    )

    assert "Parameters" in page.get_text(page.PARAMETERS_LABEL)
    assert "Click to display Parameters" in page.get_text(page.PARAMETERS_YAML_BTN)

    assert "Additional Files" in page.get_text(page.ADDITIONAL_LABEL)
    assert "Not Available" in page.get_text(page.ADDITIONAL_NA)

    assert "Owner" in page.get_text(page.OWNER_LABEL)
    if user_id == CONTAINER_OWNER:
        assert "You" in page.get_text(page.OWNER_VALUE)
    else:
        assert str(CONTAINER_OWNER) in page.get_text(page.OWNER_VALUE)

    container_created = page.get_attribute(page.CREATED, "data-date")
    assert "Created" in page.get_text(page.CREATED_LABEL)
    assert (
        datetime.datetime.strptime(container_created, "%Y-%m-%d %H:%M:%S")
        == container_mock.created_at
    )

    container_modified = page.get_attribute(page.MODIFIED, "data-date")
    assert "Modified" in page.get_text(page.MODIFIED_LABEL)
    assert (
        datetime.datetime.strptime(container_modified, "%Y-%m-%d %H:%M:%S")
        == container_mock.modified_at
    )


def test_container_details_backend_calls(page, mocker):
    c = _make_container_mock()
    spy_get = mocker.patch(PATCH_CUBE_GET, return_value=c)
    mocker.patch(PATCH_READ_USER_ACCOUNT, return_value={"email": "ui@test.local"})
    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    spy_get.assert_called_once_with(cube_uid=CONTAINER_ID, valid_only=False)


@pytest.mark.parametrize("user_id", [CONTAINER_OWNER, CONTAINER_OWNER + 1])
@pytest.mark.parametrize("state", ["OPERATION", "DEVELOPMENT"])
def test_container_details_state(page, mocker, container_mock, user_id, state):
    container_mock.state = state
    _patch_user(mocker, user_id)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    badges = page.driver.find_elements(*page.STATE_BADGES)
    assert len(badges) >= 1
    state_text = badges[0].text
    if state == "OPERATION":
        assert state_text == "OPERATIONAL"
        assert "green" in badges[0].get_attribute("class")
    else:
        assert state_text == state
        assert "yellow" in badges[0].get_attribute("class")


@pytest.mark.parametrize("user_id", [CONTAINER_OWNER, CONTAINER_OWNER + 1])
@pytest.mark.parametrize("is_valid", [True, False])
def test_container_details_validity(page, mocker, container_mock, user_id, is_valid):
    container_mock.is_valid = is_valid
    _patch_user(mocker, user_id)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    badges = page.driver.find_elements(*page.STATE_BADGES)
    assert len(badges) >= 2
    valid_el = badges[1]
    if is_valid:
        assert valid_el.text == "VALID"
        assert "green" in valid_el.get_attribute("class")
    else:
        assert valid_el.text == "INVALID"
        assert "red" in valid_el.get_attribute("class")


@pytest.mark.parametrize("user_id", [CONTAINER_OWNER, CONTAINER_OWNER + 1])
@pytest.mark.parametrize(
    "additional_url",
    [None, "http://test.com/test.tar.gz"],
)
def test_container_details_additional_files(
    page, mocker, container_mock, user_id, additional_url
):
    container_mock.additional_files_tarball_url = additional_url
    _patch_user(mocker, user_id)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    assert "Additional Files" in page.get_text(page.ADDITIONAL_LABEL)

    if additional_url:
        link = page.find(page.ADDITIONAL_LINK)
        assert link.get_attribute("href") == additional_url
        assert link.get_attribute("target") == "_blank"
        assert "Click to Download" in link.text
    else:
        assert "Not Available" in page.get_text(page.ADDITIONAL_NA)


def test_container_details_parameters_not_available(page, mocker, container_mock):
    container_mock.parameters_config = None
    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    assert "Not Available" in page.get_text(page.PARAMETERS_NA)


def test_container_details_owner_manage_access_when_encrypted(
    page, mocker, container_mock
):
    container_mock.is_encrypted.return_value = True
    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    page.wait_for_presence_selector(page.MANAGE_ACCESS)
    assert "Manage Access" in page.get_text(page.MANAGE_ACCESS)


def test_container_details_non_owner_encrypted_access_pending(
    page, mocker, container_mock
):
    container_mock.is_encrypted.return_value = True
    mocker.patch(
        "medperf.web_ui.containers.routes.check_access_to_container",
        return_value={"has_access": False, "reason": "test reason"},
    )
    _patch_user(mocker, CONTAINER_OWNER + 99)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    page.wait_for_presence_selector(page.ACCESS_SECTION)
    assert "Access Pending" in page.driver.page_source


def test_container_details_invalid_card_when_invalid(page, mocker, container_mock):
    container_mock.is_valid = False
    _patch_user(mocker, CONTAINER_OWNER)

    page.open(BASE_URL.format(f"/containers/ui/display/{CONTAINER_ID}"))

    detail_card = page.driver.find_element("css selector", "div.invalid-card")
    assert detail_card is not None
