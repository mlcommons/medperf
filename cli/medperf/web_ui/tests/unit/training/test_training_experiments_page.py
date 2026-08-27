import datetime

import pytest
import selenium.common.exceptions as selenium_exceptions

from medperf.tests.mocks.training_exp import TestTrainingExp
from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.training.ui_page import TrainingPage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode

BASE_URL = tests_config.BASE_URL
PATCH_GET_TRAINING = "medperf.entities.training_exp.TrainingExp.all"
PATCH_GET_TRAINING_COUNT = "medperf.entities.training_exp.TrainingExp.get_count"
PATCH_GET_USER_ID = "medperf.web_ui.training.routes.get_medperf_user_data"
USER_ID = 1
PAGINATION = {"limit": 9, "offset": 0, "ordering": "-created_at"}

TEST_TRAINING_EXPS = [
    TestTrainingExp(
        id=1,
        owner=1,
        name="tr1",
        state="DEVELOPMENT",
        approval_status="APPROVED",
        created_at=datetime.datetime(2025, 1, 1),
    ),
    TestTrainingExp(
        id=2,
        owner=2,
        name="tr2",
        state="OPERATION",
        approval_status="PENDING",
        created_at=datetime.datetime(2025, 2, 2),
    ),
]


@pytest.fixture
def page(driver):
    return TrainingPage(driver)


def test_empty_training_ui_page_content(page, mocker):
    filters = {"owner": USER_ID, **PAGINATION}
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_TRAINING_COUNT, return_value=0)
    spy_training = mocker.patch(PATCH_GET_TRAINING, return_value=[])

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui"))

    spy_training.assert_called_with(filters=PAGINATION)
    assert page.get_text(page.HEADER) == "Training Experiments"
    assert page.get_text(page.REG_TRAINING_BTN) == "Register New Training Experiment"
    assert page.get_text(page.MINE_LABEL) == "Mine only"
    assert (
        page.get_attribute(page.MINE_INPUT, "data-entity-name")
        == "training experiments"
    )
    assert page.get_text(page.NO_EXPERIMENTS) == "No training experiments found"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)
    assert page.is_mine()
    spy_training.assert_called_with(filters=filters)

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)
    assert page.not_mine()
    spy_training.assert_called_with(filters=PAGINATION)


def test_training_ui_page_content(page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_TRAINING_COUNT, return_value=len(TEST_TRAINING_EXPS))
    mocker.patch(PATCH_GET_TRAINING, return_value=TEST_TRAINING_EXPS)

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui"))

    with pytest.raises(selenium_exceptions.NoSuchElementException):
        page.driver.find_element(*page.NO_EXPERIMENTS)

    cards = page.find_elements(page.CARDS_CONTAINER)
    assert len(cards) == 2
    for card in cards:
        exp_id_txt = card.find_element(*page.CARD_ID).text
        exp_state = card.find_element(*page.CARD_STATE).text
        exp_approval = card.find_element(*page.CARD_APPROVAL).text
        assert exp_id_txt.startswith("ID:")
        assert exp_state in ("OPERATIONAL", "DEVELOPMENT")
        assert exp_approval.startswith("Approval:")


def test_training_ui_page_search_sort_pagination(page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_TRAINING_COUNT, return_value=30)
    spy_training = mocker.patch(PATCH_GET_TRAINING, return_value=TEST_TRAINING_EXPS)

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui"))

    old_url = page.current_url
    page.search("tr1")
    page.wait_for_url_change(old_url)

    assert "search=tr1" in page.current_url
    spy_training.assert_called_with(filters={"search": "tr1", **PAGINATION})

    old_url = page.current_url
    page.set_ordering("Name A–Z")
    page.wait_for_url_change(old_url)

    spy_training.assert_called_with(
        filters={"search": "tr1", "limit": 9, "offset": 0, "ordering": "name"}
    )

    old_url = page.current_url
    page.set_page_size(24)
    page.wait_for_url_change(old_url)

    spy_training.assert_called_with(
        filters={"search": "tr1", "limit": 24, "offset": 0, "ordering": "name"}
    )

    old_url = page.current_url
    page.click(page.page_link(2))
    page.wait_for_url_change(old_url)

    spy_training.assert_called_with(
        filters={"search": "tr1", "limit": 24, "offset": 24, "ordering": "name"}
    )
