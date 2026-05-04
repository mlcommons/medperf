from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.container.ui_page import ContainersPage

import datetime
import pytest
from medperf.tests.mocks.cube import TestCube
import selenium.common.exceptions as selenium_exceptions

BASE_URL = tests_config.BASE_URL
PATCH_GET_CONTAINERS = "medperf.entities.cube.Cube.all"
PATCH_GET_USER_ID = "medperf.web_ui.containers.routes.get_medperf_user_data"
USER_ID = 1

TEST_CONTAINERS = {
    "1": TestCube(
        id=1, owner=1, created_at=datetime.datetime(2025, 1, 1), name="test_container1"
    ),
    "2": TestCube(
        id=2, owner=2, created_at=datetime.datetime(2025, 2, 2), name="test_container2"
    ),
    "3": TestCube(
        id=3, owner=3, created_at=datetime.datetime(2025, 3, 3), is_valid=False
    ),
}


@pytest.fixture
def page(driver):
    return ContainersPage(driver)


def test_empty_containers_ui_page_content(page, mocker):
    filters = {"owner": USER_ID}

    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    spy_containers = mocker.patch(PATCH_GET_CONTAINERS, return_value=[])

    page.open(BASE_URL.format("/containers/ui"))

    spy_containers.assert_called_with(filters={})
    assert page.get_text(page.REG_DSET_BTN) == "Register a New Container"
    assert page.get_text(page.HEADER) == "Containers"
    assert page.get_text(page.MINE_LABEL) == "Show only my containers"
    assert page.get_text(page.NO_CONTAINERS) == "No containers yet"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "containers"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.is_mine()
    spy_containers.assert_called_with(filters=filters)

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.not_mine()
    spy_containers.assert_called_with(filters={})


def test_containers_ui_page_content(page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_CONTAINERS, return_value=list(TEST_CONTAINERS.values()))

    page.open(BASE_URL.format("/containers/ui"))

    with pytest.raises(selenium_exceptions.NoSuchElementException):
        page.driver.find_element(*page.NO_CONTAINERS)

    containers_cards = page.find_elements(page.CARDS_CONTAINER)

    assert len(containers_cards) == len(TEST_CONTAINERS)

    for container in containers_cards:
        cont_name = container.find_element(*page.CARD_TITLE).text
        cont_url = container.find_element(*page.CARD_TITLE).get_attribute("href")
        cont_id_txt = container.find_element(*page.CARD_ID).text
        cont_state = container.find_element(*page.CARD_STATE).text
        cont_valid_txt = container.find_element(*page.CARD_VALID).text.strip()
        cont_created = container.find_element(*page.CARD_CREATED).get_attribute(
            "data-date"
        )

        cont_id = cont_id_txt.split(":")[-1].strip()
        cont_id_url = cont_url.split("/")[-1].strip()
        cont_created_dt = datetime.datetime.strptime(cont_created, "%Y-%m-%d %H:%M:%S")

        assert cont_id_txt.startswith("ID:")
        assert cont_valid_txt in ("Valid", "Invalid")

        assert cont_id == cont_id_url
        assert cont_id.isdigit()

        assert cont_name == TEST_CONTAINERS[cont_id].name
        assert cont_id == str(TEST_CONTAINERS[cont_id].id)
        assert cont_url.endswith(f"/containers/ui/display/{cont_id}")
        assert (cont_valid_txt == "Valid") == TEST_CONTAINERS[cont_id].is_valid
        assert cont_created_dt == TEST_CONTAINERS[cont_id].created_at

        if TEST_CONTAINERS[cont_id].is_valid:
            assert "invalid-card" not in container.get_attribute("class")
        else:
            assert "invalid-card" in container.get_attribute("class")

        if TEST_CONTAINERS[cont_id].state == "OPERATION":
            assert cont_state == "OPERATIONAL"
        else:
            assert cont_state == TEST_CONTAINERS[cont_id].state

    assert page.get_text(page.REG_DSET_BTN) == "Register a New Container"
    assert page.get_text(page.HEADER) == "Containers"
    assert page.get_text(page.MINE_LABEL) == "Show only my containers"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "containers"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.is_mine()

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.not_mine()
