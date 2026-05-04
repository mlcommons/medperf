import datetime
from unittest.mock import MagicMock

from medperf.tests.mocks.cube import TestCube
import pytest
from selenium.webdriver.common.by import By

from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.training_exp import TestTrainingExp
from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.dataset.details_page import DatasetDetailsPage
from medperf.web_ui.tests.pages.dataset.register_page import RegDatasetPage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode

BASE_URL = tests_config.BASE_URL


def _patch_common(mocker):
    data = {"id": 1, "email": "training-ui-test@local"}
    mocker.patch(
        "medperf.web_ui.common.read_user_account", return_value={"email": data["email"]}
    )
    mocker.patch("medperf.web_ui.common.get_medperf_user_data", return_value=data)
    mocker.patch(
        "medperf.web_ui.datasets.routes.get_medperf_user_data", return_value=data
    )
    user_obj = MagicMock()
    user_obj.id = 1
    user_obj.is_cc_initialized.return_value = True
    user_obj.get_cc_config.return_value = {}
    mocker.patch(
        "medperf.web_ui.datasets.routes.get_medperf_user_object", return_value=user_obj
    )


@pytest.fixture
def reg_page(driver):
    return RegDatasetPage(driver)


@pytest.fixture
def details_page(driver):
    return DatasetDetailsPage(driver)


def test_dataset_registration_page_differs_by_mode(reg_page, mocker):
    _patch_common(mocker)
    mocker.patch("medperf.entities.benchmark.Benchmark.all", return_value=[])

    switch_to_ui_mode(reg_page, "evaluation")
    reg_page.open(BASE_URL.format("/datasets/register/ui"))
    reg_page.wait_for_presence_selector(reg_page.BENCHMARK)
    assert reg_page.driver.find_elements(*reg_page.DATA_PREP) == []

    mocker.patch(
        "medperf.entities.cube.Cube.all", return_value=[TestCube(id=1, name="prep")]
    )
    mocker.patch(
        "medperf.web_ui.datasets.routes.get_container_type",
        return_value="data-prep-container",
    )

    switch_to_ui_mode(reg_page, "training")
    reg_page.open(BASE_URL.format("/datasets/register/ui"))
    reg_page.wait_for_presence_selector(reg_page.DATA_PREP)
    assert reg_page.driver.find_elements(*reg_page.BENCHMARK) == []
    assert reg_page.get_text(reg_page.DATA_PREP_LABEL) == "Data Preparation Container"


def test_dataset_details_training_actions(details_page, mocker):
    _patch_common(mocker)
    dataset = TestDataset(
        id=31,
        owner=1,
        name="dataset-31",
        data_preparation_mlcube=1,
        state="OPERATION",
        is_valid=True,
        created_at=datetime.datetime(2026, 2, 1),
        modified_at=datetime.datetime(2026, 2, 2),
    )
    dataset.read_report = lambda: None
    dataset.read_statistics = lambda: None
    dataset.is_ready = lambda: True
    dataset.is_operational = lambda: True
    dataset.get_cc_config = lambda: {}
    dataset.is_cc_configured = lambda: False
    dataset.is_cc_initialized = lambda: True
    dataset.get_last_synced = lambda: None
    dataset.report_path = ""
    dataset.report = {}
    dataset.generated_metadata = {}

    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(
        "medperf.web_ui.datasets.routes.get_user_associations",
        return_value=[
            {"training_exp": 55, "dataset": 31, "approval_status": "APPROVED"}
        ],
    )
    mocker.patch(
        "medperf.entities.training_exp.TrainingExp.all",
        return_value=[TestTrainingExp(id=55, name="tr-55", data_preparation_mlcube=1)],
    )
    mocker.patch(
        "medperf.entities.training_exp.TrainingExp.get",
        return_value=TestTrainingExp(id=55, name="tr-55", data_preparation_mlcube=1),
    )

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))
    assert details_page.get_text(details_page.HEADER) == "dataset-31"
    assert details_page.get_text(details_page.SUB_HEADER_1) == "Details"
    assert details_page.get_text(details_page.ID_LABEL) == "Dataset ID"
    assert details_page.get_text(details_page.ID) == "31"
    assert details_page.get_text(details_page.OWNER_LABEL) == "Owner"
    assert (
        details_page.get_text(details_page.DATA_PREP_LABEL)
        == "Data Preparation Container"
    )
    assert details_page.get_text(details_page.STATE) == "OPERATIONAL"
    assert details_page.get_text(details_page.VALID) == "VALID"
    details_page.wait_for_presence_selector((By.ID, "dropdown-training-div"))
    details_page.wait_for_presence_selector(
        (By.CSS_SELECTOR, "form[id^='start-training-form-']")
    )
    start_form = details_page.find(
        (By.CSS_SELECTOR, "form[id^='start-training-form-']")
    )
    training_input = start_form.find_element(
        By.CSS_SELECTOR, "input[name='training_exp_id']"
    )
    assert training_input.get_attribute("value") == "55"
    details_page.wait_for_presence_selector((By.ID, "stop-training-btn"))
