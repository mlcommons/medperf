import pytest
from selenium.webdriver.common.by import By

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.base_page import BasePage
from medperf.web_ui.tests.unit.helpers import patch_medperf_session, switch_to_ui_mode

BASE_URL = tests_config.BASE_URL


@pytest.fixture
def page(driver):
    return BasePage(driver)


def test_navbar_mode_specific_links(page, mocker):
    patch_medperf_session(
        mocker,
        email="training-ui-test@local",
        route_modules=("benchmarks", "training"),
        with_user_object=True,
    )
    mocker.patch("medperf.entities.benchmark.Benchmark.all", return_value=[])
    mocker.patch("medperf.entities.benchmark.Benchmark.get_count", return_value=0)

    page.open(BASE_URL.format("/benchmarks/ui"))
    page.wait_for_presence_selector(
        (By.CSS_SELECTOR, "[data-testid='navbar-link-benchmarks']")
    )
    assert (
        page.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='navbar-link-experiments']"
        )
        == []
    )
    assert (
        page.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='navbar-link-aggregators']"
        )
        == []
    )

    switch_to_ui_mode(page, "training")
    mocker.patch("medperf.entities.training_exp.TrainingExp.all", return_value=[])
    mocker.patch("medperf.entities.training_exp.TrainingExp.get_count", return_value=0)
    page.open(BASE_URL.format("/training/ui"))

    page.wait_for_presence_selector(
        (By.CSS_SELECTOR, "[data-testid='navbar-link-experiments']")
    )
    page.wait_for_presence_selector(
        (By.CSS_SELECTOR, "[data-testid='navbar-link-aggregators']")
    )
    assert (
        page.driver.find_elements(
            By.CSS_SELECTOR, "[data-testid='navbar-link-benchmarks']"
        )
        == []
    )
    assert (
        page.driver.find_elements(By.CSS_SELECTOR, "[data-testid='navbar-link-models']")
        == []
    )
