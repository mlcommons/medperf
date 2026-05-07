from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.dataset.ui_page import DatasetsPage

import datetime
import pytest
from medperf.tests.mocks.dataset import TestDataset
import selenium.common.exceptions as selenium_exceptions

BASE_URL = tests_config.BASE_URL
PATCH_GET_DATASETS = "medperf.entities.dataset.Dataset.all"
PATCH_GET_USER_ID = "medperf.web_ui.datasets.routes.get_medperf_user_data"
USER_ID = 1

TEST_DATASETS = {
    "1": TestDataset(
        id=1,
        owner=1,
        created_at=datetime.datetime(2025, 1, 1),
        name="test_dataset1",
        location="test_location1",
        description="test description",
        state="DEVELOPMENT",
    ),
    "2": TestDataset(
        id=2,
        owner=2,
        created_at=datetime.datetime(2025, 2, 2),
        name="test_dataset2",
        location="test_location2",
        description="test description 2",
    ),
    "3": TestDataset(
        id=3, owner=3, created_at=datetime.datetime(2025, 3, 3), is_valid=False
    ),
}


@pytest.fixture
def page(driver):
    return DatasetsPage(driver)


def test_empty_datasets_ui_page_content(page, mocker):
    filters = {"owner": USER_ID}

    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    spy_datasets = mocker.patch(PATCH_GET_DATASETS, return_value=[])

    page.open(BASE_URL.format("/datasets/ui"))

    spy_datasets.assert_called_with(filters={})
    assert page.get_text(page.REG_DSET_BTN) == "Register a New Dataset"
    assert page.get_text(page.IMPORT_DSET_BTN) == "Import Dataset"
    assert page.get_text(page.HEADER) == "Datasets"
    assert page.get_text(page.MINE_LABEL) == "Show only my datasets"
    assert page.get_text(page.NO_DATASETS) == "No datasets yet"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "datasets"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.is_mine()
    spy_datasets.assert_called_with(filters=filters)

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.not_mine()
    spy_datasets.assert_called_with(filters={})

    assert spy_datasets.call_count == 3


def test_datasets_ui_page_content(page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_DATASETS, return_value=list(TEST_DATASETS.values()))

    page.open(BASE_URL.format("/datasets/ui"))

    with pytest.raises(selenium_exceptions.NoSuchElementException):
        page.driver.find_element(*page.NO_DATASETS)

    dataset_cards = page.find_elements(page.CARDS_CONTAINER)

    assert len(dataset_cards) == len(TEST_DATASETS)

    for dataset in dataset_cards:
        dset_name = dataset.find_element(*page.CARD_TITLE).text
        dset_url = dataset.find_element(*page.CARD_TITLE).get_attribute("href")
        dset_id_txt = dataset.find_element(*page.CARD_ID).text
        dset_state = dataset.find_element(*page.CARD_STATE).text
        dset_valid_txt = dataset.find_element(*page.CARD_VALID).text.strip()
        dset_desc_txt = dataset.find_element(*page.CARD_DESC).text
        dset_created = dataset.find_element(*page.CARD_CREATED).get_attribute(
            "data-date"
        )
        dset_location_txt = dataset.find_element(*page.CARD_LOCATION).text

        dset_id = dset_id_txt.split(":")[-1].strip()
        dset_id_url = dset_url.split("/")[-1].strip()
        dset_desc = dset_desc_txt.split(":", 1)[-1].strip()
        dset_created_dt = datetime.datetime.strptime(dset_created, "%Y-%m-%d %H:%M:%S")
        dset_location = dset_location_txt.split(":")[-1].strip()

        assert dset_id_txt.startswith("ID:")
        assert dset_valid_txt in ("Valid", "Invalid")
        assert dset_desc_txt.startswith("Description:")
        assert dset_location_txt.startswith("Location:")

        assert dset_id == dset_id_url
        assert dset_id.isdigit()

        assert dset_name == TEST_DATASETS[dset_id].name
        assert dset_id == str(TEST_DATASETS[dset_id].id)
        assert dset_url.endswith(f"/datasets/ui/display/{dset_id}")
        assert (dset_valid_txt == "Valid") == TEST_DATASETS[dset_id].is_valid
        assert dset_desc == str(TEST_DATASETS[dset_id].description)
        assert dset_created_dt == TEST_DATASETS[dset_id].created_at
        assert dset_location == TEST_DATASETS[dset_id].location

        if TEST_DATASETS[dset_id].is_valid:
            assert "invalid-card" not in dataset.get_attribute("class")
        else:
            assert "invalid-card" in dataset.get_attribute("class")

        if TEST_DATASETS[dset_id].state == "OPERATION":
            assert dset_state == "OPERATIONAL"
        else:
            assert dset_state == TEST_DATASETS[dset_id].state

    assert page.get_text(page.REG_DSET_BTN) == "Register a New Dataset"
    assert page.get_text(page.IMPORT_DSET_BTN) == "Import Dataset"
    assert page.get_text(page.HEADER) == "Datasets"
    assert page.get_text(page.MINE_LABEL) == "Show only my datasets"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "datasets"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.is_mine()

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.not_mine()
