import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from medperf.tests.mocks.training_exp import TestTrainingExp
import pytest
from selenium.common.exceptions import NoSuchElementException

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.aggregator.details_page import AggregatorDetailsPage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode

BASE_URL = tests_config.BASE_URL

TEST_TRAINING_EXPS = [TestTrainingExp(id=77, name="tr-77")]


@pytest.fixture(autouse=True)
def patch_login(mocker):
    mocker.patch(
        "medperf.web_ui.aggregators.routes.get_medperf_user_data",
        return_value={"id": 1, "email": "training-ui-test@local"},
    )
    mocker.patch(
        "medperf.web_ui.common.read_user_account",
        return_value={"email": "training-ui-test@local"},
    )
    mocker.patch(
        "medperf.web_ui.common.get_medperf_user_data",
        return_value={"id": 1, "email": "training-ui-test@local"},
    )


@pytest.fixture
def page(driver):
    return AggregatorDetailsPage(driver)


def test_aggregator_details_page_common_content(page, mocker):
    agg = SimpleNamespace(
        id=9,
        name="agg-9",
        owner=1,
        address="127.0.0.1",
        port=7000,
        admin_port=7001,
        created_at=datetime.datetime(2026, 1, 1),
        modified_at=datetime.datetime(2026, 1, 2),
        get_training_experiments=lambda: [TEST_TRAINING_EXPS],
    )
    mocker.patch("medperf.entities.aggregator.Aggregator.get", return_value=agg)
    mocker.patch("medperf.entities.ca.CA.get", return_value=MagicMock(id=1))
    mocker.patch("medperf.web_ui.aggregators.routes.os.path.exists", return_value=False)

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui/display/9"))

    assert page.get_text(page.HEADER) == "agg-9"
    assert page.get_text(page.DETAILS_HEADING) == "Details"
    assert page.get_text(page.ID_LABEL) == "Aggregator ID"
    assert page.get_text(page.ID) == "9"
    assert page.get_text(page.OWNER_LABEL) == "Owner"
    assert page.get_text(page.ADDRESS_LABEL) == "Address"
    assert page.get_text(page.ADDRESS) == "127.0.0.1"
    assert page.get_text(page.PORT_LABEL) == "Port"
    assert page.get_text(page.PORT) == "7000"
    assert page.get_text(page.ADMIN_PORT_LABEL) == "Admin Port"
    assert page.get_text(page.ADMIN_PORT) == "7001"
    assert page.get_text(page.EXPERIMENTS_HEADING) == "Training experiments"
    assert page.get_text(page.ACTIONS_HEADING) == "Actions"
    page.wait_for_presence_selector(page.GET_CERT_FORM)
    page.wait_for_presence_selector(page.START_FORM)
    page.wait_for_presence_selector(page.STOP_BTN)


def test_aggregator_details_page_non_owner_content(page, mocker):
    agg = SimpleNamespace(
        id=9,
        name="agg-9",
        owner=2,
        address="127.0.0.1",
        port=7000,
        admin_port=7001,
        created_at=datetime.datetime(2026, 1, 1),
        modified_at=datetime.datetime(2026, 1, 2),
        get_training_experiments=lambda: [],
    )
    mocker.patch("medperf.entities.aggregator.Aggregator.get", return_value=agg)

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui/display/9"))

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.ACTIONS_HEADING)
