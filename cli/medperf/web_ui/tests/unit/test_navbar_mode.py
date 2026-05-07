from unittest.mock import MagicMock

import pytest
from selenium.webdriver.common.by import By

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.base_page import BasePage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode

BASE_URL = tests_config.BASE_URL


def _patch_medperf_session(mocker, user_id: int = 1):
    data = {"id": user_id, "email": "training-ui-test@local"}
    mocker.patch(
        "medperf.web_ui.common.read_user_account", return_value={"email": data["email"]}
    )
    mocker.patch("medperf.web_ui.common.get_medperf_user_data", return_value=data)
    mocker.patch(
        "medperf.web_ui.benchmarks.routes.get_medperf_user_data", return_value=data
    )
    mocker.patch(
        "medperf.web_ui.training.routes.get_medperf_user_data", return_value=data
    )
    user_obj = MagicMock()
    user_obj.id = user_id
    user_obj.is_cc_initialized.return_value = True
    user_obj.get_cc_config.return_value = {}
    mocker.patch(
        "medperf.web_ui.datasets.routes.get_medperf_user_object", return_value=user_obj
    )


@pytest.fixture
def page(driver):
    return BasePage(driver)


def test_navbar_mode_specific_links(page, mocker):
    _patch_medperf_session(mocker)
    mocker.patch("medperf.entities.benchmark.Benchmark.all", return_value=[])

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
