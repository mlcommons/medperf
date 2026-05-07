import datetime

import pytest
import selenium.common.exceptions as selenium_exceptions

from medperf.tests.mocks.training_exp import TestTrainingExp
from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.training.ui_page import TrainingPage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode

BASE_URL = tests_config.BASE_URL
PATCH_GET_TRAINING = "medperf.entities.training_exp.TrainingExp.all"
PATCH_GET_USER_ID = "medperf.web_ui.training.routes.get_medperf_user_data"
USER_ID = 1

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


def _patch_common(mocker):
    data = {"id": USER_ID, "email": "training-ui-test@local"}
    mocker.patch(
        "medperf.web_ui.common.read_user_account", return_value={"email": data["email"]}
    )
    mocker.patch("medperf.web_ui.common.get_medperf_user_data", return_value=data)
    mocker.patch(PATCH_GET_USER_ID, return_value=data)


@pytest.fixture
def ui_page(driver):
    return TrainingPage(driver)


def test_empty_training_ui_page_content(ui_page, mocker):
    filters = {"owner": USER_ID}
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    spy_training = mocker.patch(PATCH_GET_TRAINING, return_value=[])

    switch_to_ui_mode(ui_page, "training")
    ui_page.open(BASE_URL.format("/training/ui"))

    spy_training.assert_called_with(filters={})
    assert ui_page.get_text(ui_page.HEADER) == "Training Experiments"
    assert (
        ui_page.get_text(ui_page.REG_TRAINING_BTN) == "Register New Training Experiment"
    )
    assert ui_page.get_text(ui_page.MINE_LABEL) == "Show only my experiments"
    assert ui_page.get_attribute(ui_page.MINE_INPUT, "data-entity-name") == "training"
    assert ui_page.get_text(ui_page.NO_EXPERIMENTS) == "No training experiments yet"

    old_url = ui_page.current_url
    ui_page.toggle_mine()
    ui_page.wait_for_url_change(old_url)
    assert ui_page.is_mine()
    spy_training.assert_called_with(filters=filters)

    old_url = ui_page.current_url
    ui_page.toggle_mine()
    ui_page.wait_for_url_change(old_url)
    assert ui_page.not_mine()
    spy_training.assert_called_with(filters={})


def test_training_ui_page_content(ui_page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_TRAINING, return_value=TEST_TRAINING_EXPS)

    switch_to_ui_mode(ui_page, "training")
    ui_page.open(BASE_URL.format("/training/ui"))

    with pytest.raises(selenium_exceptions.NoSuchElementException):
        ui_page.driver.find_element(*ui_page.NO_EXPERIMENTS)

    cards = ui_page.find_elements(ui_page.CARDS_CONTAINER)
    assert len(cards) == 2
    for card in cards:
        exp_id_txt = card.find_element(*ui_page.CARD_ID).text
        exp_state = card.find_element(*ui_page.CARD_STATE).text
        exp_approval = card.find_element(*ui_page.CARD_APPROVAL).text
        assert exp_id_txt.startswith("ID:")
        assert exp_state in ("OPERATIONAL", "DEVELOPMENT")
        assert exp_approval.startswith("Approval:")
