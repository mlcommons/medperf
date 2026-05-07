import datetime

import pytest
import selenium.common.exceptions as selenium_exceptions

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.aggregator.ui_page import AggregatorsPage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode

BASE_URL = tests_config.BASE_URL
PATCH_GET_AGGS = "medperf.entities.aggregator.Aggregator.all"
PATCH_GET_USER_ID = "medperf.web_ui.aggregators.routes.get_medperf_user_data"
USER_ID = 1


class _TestAggregator:
    def __init__(self, id, owner, created_at, name, address, port):
        self.id = id
        self.owner = owner
        self.created_at = created_at
        self.name = name
        self.address = address
        self.port = port


TEST_AGGREGATORS = {
    "1": _TestAggregator(
        id=1,
        owner=1,
        created_at=datetime.datetime(2025, 1, 1),
        name="agg1",
        address="127.0.0.1",
        port=7000,
    ),
    "2": _TestAggregator(
        id=2,
        owner=2,
        created_at=datetime.datetime(2025, 2, 2),
        name="agg2",
        address="10.0.0.1",
        port=7100,
    ),
}


@pytest.fixture
def page(driver):
    return AggregatorsPage(driver)


def test_empty_aggregators_ui_page_content(page, mocker):
    filters = {"owner": USER_ID}
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    spy_aggs = mocker.patch(PATCH_GET_AGGS, return_value=[])

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui"))

    spy_aggs.assert_called_with(filters={})
    assert page.get_text(page.REG_AGG_BTN) == "Register New Aggregator"
    assert page.get_text(page.HEADER) == "Aggregators"
    assert page.get_text(page.MINE_LABEL) == "Show only my aggregators"
    assert page.get_text(page.NO_AGGREGATORS) == "No aggregators yet"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "aggregators"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)
    assert page.is_mine()
    spy_aggs.assert_called_with(filters=filters)

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)
    assert page.not_mine()
    spy_aggs.assert_called_with(filters={})


def test_aggregators_ui_page_content(page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_AGGS, return_value=list(TEST_AGGREGATORS.values()))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui"))

    with pytest.raises(selenium_exceptions.NoSuchElementException):
        page.driver.find_element(*page.NO_AGGREGATORS)

    cards = page.find_elements(page.CARDS_CONTAINER)
    assert len(cards) == len(TEST_AGGREGATORS)

    for card in cards:
        agg_name = card.find_element(*page.CARD_TITLE).text
        agg_url = card.find_element(*page.CARD_TITLE).get_attribute("href")
        agg_id_txt = card.find_element(*page.CARD_ID).text
        agg_address_txt = card.find_element(*page.CARD_ADDRESS).text
        agg_created = card.find_element(*page.CARD_CREATED).get_attribute("data-date")

        agg_id = agg_id_txt.split(":")[-1].strip()
        agg_id_url = agg_url.split("/")[-1].strip()
        agg_address = agg_address_txt.split(":", 1)[-1].strip()
        agg_created_dt = datetime.datetime.strptime(agg_created, "%Y-%m-%d %H:%M:%S")

        assert agg_id_txt.startswith("ID:")
        assert agg_address_txt.startswith("Address:")
        assert agg_id == agg_id_url
        assert agg_id.isdigit()
        assert agg_name == TEST_AGGREGATORS[agg_id].name
        assert agg_created_dt == TEST_AGGREGATORS[agg_id].created_at
        assert agg_address == (
            f"{TEST_AGGREGATORS[agg_id].address}:{TEST_AGGREGATORS[agg_id].port}"
        )

    assert page.get_text(page.REG_AGG_BTN) == "Register New Aggregator"
    assert page.get_text(page.HEADER) == "Aggregators"
    assert page.get_text(page.MINE_LABEL) == "Show only my aggregators"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "aggregators"
