from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.model.ui_page import ModelsPage

import datetime
import pytest
from medperf.tests.mocks.model import TestModel
import selenium.common.exceptions as selenium_exceptions

BASE_URL = tests_config.BASE_URL
PATCH_GET_MODELS = "medperf.entities.model.Model.all"
PATCH_GET_MODELS_COUNT = "medperf.entities.model.Model.get_count"
PATCH_GET_USER_ID = "medperf.web_ui.models.routes.get_medperf_user_data"
USER_ID = 1
PAGINATION = {"limit": 9, "offset": 0, "ordering": "-created_at"}

TEST_MODELS = {
    "1": TestModel(
        id=1, owner=1, created_at=datetime.datetime(2025, 1, 1), name="test_model1"
    ),
    "2": TestModel(
        id=2, owner=2, created_at=datetime.datetime(2025, 2, 2), name="test_model2"
    ),
    "3": TestModel(
        id=3, owner=3, created_at=datetime.datetime(2025, 3, 3), is_valid=False
    ),
}


@pytest.fixture
def page(driver):
    return ModelsPage(driver)


def test_empty_models_ui_page_content(page, mocker):
    filters = {"owner": USER_ID, **PAGINATION}

    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_MODELS_COUNT, return_value=0)
    spy_models = mocker.patch(PATCH_GET_MODELS, return_value=[])

    page.open(BASE_URL.format("/models/ui"))

    spy_models.assert_called_with(filters=PAGINATION)
    assert page.get_text(page.REG_CONT_BTN) == "Register a New Container Model"
    assert page.get_text(page.REG_ASSET_BTN) == "Register a New Asset Model"
    assert page.get_text(page.HEADER) == "Models"
    assert page.get_text(page.MINE_LABEL) == "Mine only"
    assert page.get_text(page.NO_MODELS) == "No models found"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "models"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.is_mine()
    spy_models.assert_called_with(filters=filters)

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.not_mine()
    spy_models.assert_called_with(filters=PAGINATION)


def test_models_ui_page_content(page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_MODELS_COUNT, return_value=len(TEST_MODELS))
    mocker.patch(PATCH_GET_MODELS, return_value=list(TEST_MODELS.values()))

    page.open(BASE_URL.format("/models/ui"))

    with pytest.raises(selenium_exceptions.NoSuchElementException):
        page.driver.find_element(*page.NO_MODELS)

    model_cards = page.find_elements(page.CARDS_CONTAINER)

    assert len(model_cards) == len(TEST_MODELS)

    for model in model_cards:
        model_name = model.find_element(*page.CARD_TITLE).text
        model_url = model.find_element(*page.CARD_TITLE).get_attribute("href")
        model_id_txt = model.find_element(*page.CARD_ID).text
        model_type_txt = model.find_element(*page.CARD_TYPE).text
        model_state = model.find_element(*page.CARD_STATE).text
        model_valid_txt = model.find_element(*page.CARD_VALID).text.strip()
        model_created = model.find_element(*page.CARD_CREATED).get_attribute(
            "data-date"
        )

        model_id = model_id_txt.split(":")[-1].strip()
        model_id_url = model_url.split("/")[-1].strip()
        model_created_dt = datetime.datetime.strptime(
            model_created, "%Y-%m-%d %H:%M:%S"
        )

        assert model_id_txt.startswith("ID:")
        assert model_type_txt == "Type: CONTAINER"
        assert model_valid_txt in ("Valid", "Invalid")

        assert model_id == model_id_url
        assert model_id.isdigit()

        assert model_name == TEST_MODELS[model_id].name
        assert model_id == str(TEST_MODELS[model_id].id)
        assert model_url.endswith(f"/models/ui/display/{model_id}")
        assert (model_valid_txt == "Valid") == TEST_MODELS[model_id].is_valid
        assert model_created_dt == TEST_MODELS[model_id].created_at

        if TEST_MODELS[model_id].state == "OPERATION":
            assert model_state == "OPERATIONAL"
        else:
            assert model_state == TEST_MODELS[model_id].state

    assert page.get_text(page.REG_CONT_BTN) == "Register a New Container Model"
    assert page.get_text(page.REG_ASSET_BTN) == "Register a New Asset Model"
    assert page.get_text(page.HEADER) == "Models"
    assert page.get_text(page.MINE_LABEL) == "Mine only"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "models"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.is_mine()

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.not_mine()


def test_models_ui_page_search_sort_pagination(page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_MODELS_COUNT, return_value=30)
    spy_models = mocker.patch(PATCH_GET_MODELS, return_value=list(TEST_MODELS.values()))

    page.open(BASE_URL.format("/models/ui"))

    old_url = page.current_url
    page.search("test_model1")
    page.wait_for_url_change(old_url)

    assert "search=test_model1" in page.current_url
    spy_models.assert_called_with(filters={"search": "test_model1", **PAGINATION})

    old_url = page.current_url
    page.set_ordering("Name A–Z")
    page.wait_for_url_change(old_url)

    spy_models.assert_called_with(
        filters={"search": "test_model1", "limit": 9, "offset": 0, "ordering": "name"}
    )

    old_url = page.current_url
    page.set_page_size(24)
    page.wait_for_url_change(old_url)

    spy_models.assert_called_with(
        filters={"search": "test_model1", "limit": 24, "offset": 0, "ordering": "name"}
    )

    old_url = page.current_url
    page.click(page.page_link(2))
    page.wait_for_url_change(old_url)

    spy_models.assert_called_with(
        filters={"search": "test_model1", "limit": 24, "offset": 24, "ordering": "name"}
    )
