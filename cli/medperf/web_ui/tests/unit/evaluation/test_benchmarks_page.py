from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.benchmark.ui_page import BenchmarksPage

import datetime
import pytest
from medperf.tests.mocks.benchmark import TestBenchmark
import selenium.common.exceptions as selenium_exceptions

BASE_URL = tests_config.BASE_URL
PATCH_GET_BENCHMARKS = "medperf.entities.benchmark.Benchmark.all"
PATCH_GET_USER_ID = "medperf.web_ui.benchmarks.routes.get_medperf_user_data"
USER_ID = 1

TEST_BENCHMARKS = {
    "1": TestBenchmark(
        id=1,
        owner=1,
        created_at=datetime.datetime(2025, 1, 1),
        name="test_benchmark1",
        description="test description 1",
        docs_url="https://test.test/bmk_doc",
    ),
    "2": TestBenchmark(
        id=2,
        owner=2,
        created_at=datetime.datetime(2025, 2, 2),
        name="test_benchmark2",
        description="test description 2",
    ),
    "3": TestBenchmark(
        id=3, owner=3, created_at=datetime.datetime(2025, 3, 3), is_valid=False
    ),
}


@pytest.fixture
def page(driver):
    return BenchmarksPage(driver)


def test_empty_benchmarks_ui_page_content(page, mocker):
    filters = {"owner": USER_ID}

    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    spy_benchmarks = mocker.patch(PATCH_GET_BENCHMARKS, return_value=[])

    page.open(BASE_URL.format("/benchmarks/ui"))

    spy_benchmarks.assert_called_with(filters={})
    assert page.get_text(page.REG_BMK_BTN) == "Register Benchmark"
    assert page.get_text(page.HEADER) == "Benchmarks"
    assert page.get_text(page.MINE_LABEL) == "Show only my benchmarks"
    assert page.get_text(page.NO_BENCHMARKS) == "No benchmarks yet"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "benchmarks"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.is_mine()
    spy_benchmarks.assert_called_with(filters=filters)

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.not_mine()
    spy_benchmarks.assert_called_with(filters={})


def test_benchmarks_ui_page_content(page, mocker):
    mocker.patch(PATCH_GET_USER_ID, return_value={"id": USER_ID})
    mocker.patch(PATCH_GET_BENCHMARKS, return_value=list(TEST_BENCHMARKS.values()))

    page.open(BASE_URL.format("/benchmarks/ui"))

    with pytest.raises(selenium_exceptions.NoSuchElementException):
        page.driver.find_element(*page.NO_BENCHMARKS)

    benchmarks_cards = page.find_elements(page.CARDS_CONTAINER)

    assert len(benchmarks_cards) == len(TEST_BENCHMARKS)

    for benchmark in benchmarks_cards:
        bmk_name = benchmark.find_element(*page.CARD_TITLE).text
        bmk_url = benchmark.find_element(*page.CARD_TITLE).get_attribute("href")
        bmk_id_txt = benchmark.find_element(*page.CARD_ID).text
        bmk_state = benchmark.find_element(*page.CARD_STATE).text
        bmk_valid_txt = benchmark.find_element(*page.CARD_VALID).text.strip()
        bmk_desc_txt = benchmark.find_element(*page.CARD_DESC).text
        bmk_docs_txt = benchmark.find_element(*page.CARD_DOCS).text
        bmk_docs_url = benchmark.find_element(*page.CARD_DOCS).get_attribute("href")
        bmk_created = benchmark.find_element(*page.CARD_CREATED).get_attribute(
            "data-date"
        )
        bmk_approval_st_txt = benchmark.find_element(*page.APPROVAL).text

        bmk_id = bmk_id_txt.split(":")[-1].strip()
        bmk_id_url = bmk_url.split("/")[-1].strip()
        bmk_desc = bmk_desc_txt.split(":", 1)[-1].strip()
        bmk_docs_txt = bmk_docs_txt.split(":", 1)[-1].strip()
        bmk_created_dt = datetime.datetime.strptime(bmk_created, "%Y-%m-%d %H:%M:%S")
        bmk_approval_st = bmk_approval_st_txt.split(":")[-1].strip()

        assert bmk_id_txt.startswith("ID:")
        assert bmk_valid_txt in ("Valid", "Invalid")
        assert bmk_desc_txt.startswith("Description:")

        assert bmk_id == bmk_id_url
        assert bmk_id.isdigit()

        assert bmk_name == TEST_BENCHMARKS[bmk_id].name
        assert bmk_id == str(TEST_BENCHMARKS[bmk_id].id)
        assert bmk_url.endswith(f"/benchmarks/ui/display/{bmk_id}")
        assert (bmk_valid_txt == "Valid") == TEST_BENCHMARKS[bmk_id].is_valid
        assert bmk_desc == str(TEST_BENCHMARKS[bmk_id].description)
        assert bmk_created_dt == TEST_BENCHMARKS[bmk_id].created_at
        assert bmk_approval_st == str(TEST_BENCHMARKS[bmk_id].approval_status)

        if TEST_BENCHMARKS[bmk_id].is_valid:
            assert "invalid-card" not in benchmark.get_attribute("class")
        else:
            assert "invalid-card" in benchmark.get_attribute("class")

        if TEST_BENCHMARKS[bmk_id].state == "OPERATION":
            assert bmk_state == "OPERATIONAL"
        else:
            assert bmk_state == TEST_BENCHMARKS[bmk_id].state

        if bmk_docs_txt == "Not Available":
            assert TEST_BENCHMARKS[bmk_id].docs_url is None
        else:
            assert bmk_docs_txt == "Documentation"
            assert bmk_docs_url == TEST_BENCHMARKS[bmk_id].docs_url

    assert page.get_text(page.REG_BMK_BTN) == "Register Benchmark"
    assert page.get_text(page.HEADER) == "Benchmarks"
    assert page.get_text(page.MINE_LABEL) == "Show only my benchmarks"
    assert page.get_attribute(page.MINE_INPUT, "data-entity-name") == "benchmarks"

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.is_mine()

    old_url = page.current_url
    page.toggle_mine()
    page.wait_for_url_change(old_url)

    assert page.not_mine()
