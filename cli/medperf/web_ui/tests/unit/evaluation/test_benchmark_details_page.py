from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.benchmark.details_page import BenchmarkDetailsPage

import json
import datetime
import pytest
from unittest.mock import ANY
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.execution import TestExecution
from medperf.web_ui.app import web_app
from medperf.enums import Status
import medperf.web_ui.events as events_module
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from medperf.web_ui.tests.unit.helpers import parse_ui_date, stub_event_generator


@pytest.fixture(scope="module", autouse=True)
def _wait_for_nonempty_webelement_text():
    original = WebElement.text

    def _waiting_text_getter(self):
        driver = self.parent
        orig_fget = original.fget

        def _non_empty(_driver):
            return orig_fget(self).strip() != ""

        WebDriverWait(driver, 3).until(_non_empty)
        return orig_fget(self)

    WebElement.text = property(_waiting_text_getter)
    yield
    WebElement.text = original


def get_date_string():
    return (
        datetime.datetime(2025, 10, 17, tzinfo=datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


BASE_URL = tests_config.BASE_URL
PATCH_BENCHMARK = "medperf.entities.benchmark.Benchmark.{}"
PATCH_GET_CONTAINER = "medperf.entities.cube.Cube.get"
PATCH_GET_DATASET = "medperf.entities.dataset.Dataset.get"
PATCH_GET_MODEL = "medperf.entities.model.Model.get"
PATCH_GET_EXECUTIONS = "medperf.entities.execution.Execution.all"
PATCH_ROUTE = "medperf.web_ui.benchmarks.routes.{}"

TEST_BENCHMARK = TestBenchmark(
    id=1,
    owner=1,
    name="test_benchmark",
    state="OPERATION",
    is_valid=True,
    data_preparation_mlcube=1,
    reference_model=2,
    data_evaluator_mlcube=3,
    created_at=datetime.datetime(2025, 10, 15),
    modified_at=datetime.datetime(2025, 10, 17),
    demo_dataset_tarball_url="http://test.com/tarball_url",
    docs_url=None,
)

TEST_CONTAINERS = {
    "1": TestCube(
        id=1, name="data-prep", modified_at=datetime.datetime(2025, 10, 10), owner=1
    ),
    "2": TestCube(
        id=2, name="ref-model", modified_at=datetime.datetime(2025, 10, 11), owner=1
    ),
    "3": TestCube(
        id=3, name="metrics", modified_at=datetime.datetime(2025, 10, 12), owner=1
    ),
    "4": TestCube(
        id=4, name="model1", modified_at=datetime.datetime(2025, 10, 13), owner=40
    ),
    "5": TestCube(
        id=5, name="model2", modified_at=datetime.datetime(2025, 10, 14), owner=50
    ),
    "6": TestCube(
        id=6, name="model3", modified_at=datetime.datetime(2025, 10, 15), owner=60
    ),
}

TEST_DATASETS = {
    "1": TestDataset(
        id=1,
        owner=10,
        name="test_dataset1",
        state="OPERATION",
        is_valid=True,
        created_at=datetime.datetime(2025, 10, 15),
        modified_at=datetime.datetime(2025, 10, 17),
    ),
    "2": TestDataset(
        id=2,
        owner=20,
        name="test_dataset2",
        state="OPERATION",
        is_valid=True,
        created_at=datetime.datetime(2025, 10, 15),
        modified_at=datetime.datetime(2025, 10, 17),
    ),
    "3": TestDataset(
        id=3,
        owner=30,
        name="test_dataset3",
        state="OPERATION",
        is_valid=True,
        created_at=datetime.datetime(2025, 10, 15),
        modified_at=datetime.datetime(2025, 10, 17),
    ),
}

DATASETS_ASSOCS = {
    "1": {
        "id": 1,
        "metadata": {"key1": "value1", "key2": "value2"},
        "approval_status": "APPROVED",
        "approved_at": get_date_string(),
        "created_at": get_date_string(),
        "modified_at": get_date_string(),
        "priority": 0,
        "dataset": 1,
        "benchmark": 1,
        "initiated_by": 10,
    },
    "2": {
        "id": 2,
        "metadata": {"key1": "value1", "key2": "value2"},
        "approval_status": "REJECTED",
        "approved_at": get_date_string(),
        "created_at": get_date_string(),
        "modified_at": get_date_string(),
        "priority": 0,
        "dataset": 2,
        "benchmark": 1,
        "initiated_by": 20,
    },
    "3": {
        "id": 3,
        "metadata": {"key1": "value1", "key2": "value2"},
        "approval_status": "PENDING",
        "approved_at": get_date_string(),
        "created_at": get_date_string(),
        "modified_at": get_date_string(),
        "priority": 0,
        "dataset": 3,
        "benchmark": 1,
        "initiated_by": 30,
    },
}

MODELS_ASSOCS = {
    "4": {
        "id": 4,
        "metadata": {"key1": "value1", "key2": "value2"},
        "approval_status": "APPROVED",
        "approved_at": get_date_string(),
        "created_at": get_date_string(),
        "modified_at": get_date_string(),
        "priority": 0,
        "model": 4,
        "benchmark": 1,
        "initiated_by": 40,
    },
    "5": {
        "id": 5,
        "metadata": {"key1": "value1", "key2": "value2"},
        "approval_status": "REJECTED",
        "approved_at": get_date_string(),
        "created_at": get_date_string(),
        "modified_at": get_date_string(),
        "priority": 0,
        "model": 5,
        "benchmark": 1,
        "initiated_by": 50,
    },
    "6": {
        "id": 6,
        "metadata": {"key1": "value1", "key2": "value2"},
        "approval_status": "PENDING",
        "approved_at": get_date_string(),
        "created_at": get_date_string(),
        "modified_at": get_date_string(),
        "priority": 0,
        "model": 6,
        "benchmark": 1,
        "initiated_by": 60,
    },
}

RESULTS = {
    "1": TestExecution(
        approved_at=None,
        approval_status="PENDING",
        id=1,
        name="b1m4d1",
        owner=10,
        is_valid=True,
        created_at=datetime.datetime(2025, 10, 17),
        modified_at=datetime.datetime(2025, 10, 17),
        benchmark=1,
        model=4,
        dataset=1,
        model_report={"execution_status": "finished"},
        evaluation_report={"execution_status": "finished"},
        finalized=False,
        finalized_at=None,
    ),
    "2": TestExecution(
        approved_at=None,
        approval_status="APPROVED",
        id=2,
        name="b1m5d2",
        owner=20,
        is_valid=True,
        created_at=datetime.datetime(2025, 10, 17),
        modified_at=datetime.datetime(2025, 10, 17),
        benchmark=1,
        model=5,
        dataset=2,
        results={"test": 123.456, "test1": "test result"},
        model_report={"execution_status": "finished"},
        evaluation_report={"execution_status": "finished"},
        finalized=True,
        finalized_at=datetime.datetime(2025, 10, 17),
    ),
}

DATASETS_WITH_USERS = {
    "1": {
        "id": 1,
        "owner": {
            "id": 10,
            "email": "testuser@test.com",
        },
    },
    "2": {
        "id": 2,
        "owner": {
            "id": 20,
            "email": "testuser1@test.com",
        },
    },
    "3": {
        "id": 3,
        "owner": {
            "id": 30,
            "email": "testuser2@test.com",
        },
    },
}


def get_test_container(cube_uid):
    return TEST_CONTAINERS[str(cube_uid)]


def get_test_dataset(dataset_id):
    return TEST_DATASETS[str(dataset_id)]


def get_test_model(model_uid):
    return TEST_CONTAINERS[str(model_uid)]


@pytest.fixture()
def patch_bmk_details_empty_assocs_and_results(mocker):
    spy_bmk = mocker.patch(PATCH_BENCHMARK.format("get"), return_value=TEST_BENCHMARK)
    spy_datasets_assocs = mocker.patch(
        PATCH_BENCHMARK.format("get_datasets_associations"), return_value=[]
    )
    spy_models_assocs = mocker.patch(
        PATCH_BENCHMARK.format("get_models_associations"), return_value=[]
    )
    spy_results = mocker.patch(PATCH_GET_EXECUTIONS, return_value=[])
    spy_get_datasets_with_users = mocker.patch(
        PATCH_BENCHMARK.format("get_datasets_with_users"), return_value=[]
    )

    spy_container = mocker.patch(PATCH_GET_CONTAINER, side_effect=get_test_container)
    mocker.patch(PATCH_GET_MODEL, side_effect=get_test_model)

    return (
        spy_bmk,
        spy_datasets_assocs,
        spy_models_assocs,
        spy_results,
        spy_get_datasets_with_users,
        spy_container,
    )


@pytest.fixture()
def patch_bmk_details_assocs_and_results(mocker):
    spy_bmk = mocker.patch(PATCH_BENCHMARK.format("get"), return_value=TEST_BENCHMARK)
    spy_datasets_assocs = mocker.patch(
        PATCH_BENCHMARK.format("get_datasets_associations"),
        return_value=list(DATASETS_ASSOCS.values()),
    )
    spy_models_assocs = mocker.patch(
        PATCH_BENCHMARK.format("get_models_associations"),
        return_value=list(MODELS_ASSOCS.values()),
    )
    spy_results = mocker.patch(
        PATCH_GET_EXECUTIONS, return_value=list(RESULTS.values())
    )
    spy_get_datasets_with_users = mocker.patch(
        PATCH_BENCHMARK.format("get_datasets_with_users"),
        return_value=list(DATASETS_WITH_USERS.values()),
    )

    spy_container = mocker.patch(PATCH_GET_CONTAINER, side_effect=get_test_container)
    spy_dataset = mocker.patch(PATCH_GET_DATASET, side_effect=get_test_dataset)
    mocker.patch(PATCH_GET_MODEL, side_effect=get_test_model)

    return (
        spy_bmk,
        spy_datasets_assocs,
        spy_models_assocs,
        spy_results,
        spy_get_datasets_with_users,
        spy_container,
        spy_dataset,
    )


@pytest.fixture()
def patch_owner(mocker):
    mocker.patch(
        PATCH_ROUTE.format("get_medperf_user_data"),
        return_value={"id": TEST_BENCHMARK.owner},
    )


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification

    return (init, reset, notifs)


@pytest.fixture
def page(driver):
    return BenchmarkDetailsPage(driver)


@pytest.mark.parametrize("user", [TEST_BENCHMARK.owner, TEST_BENCHMARK.owner + 1])
def test_benchmark_details_common_content(
    page, mocker, user, patch_bmk_details_empty_assocs_and_results
):
    data_prep_cube = str(TEST_BENCHMARK.data_preparation_mlcube)
    ref_model_cube = str(TEST_BENCHMARK.reference_model)
    metrics_cube = str(TEST_BENCHMARK.data_evaluator_mlcube)

    mocker.patch(PATCH_ROUTE.format("get_medperf_user_data"), return_value={"id": user})

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    page.wait_for_presence_selector(page.RESULT_MODAL)

    assert page.get_text(page.HEADER) == TEST_BENCHMARK.name
    assert "Details" in page.get_text(page.SUB_HEADER_1)

    assert page.get_text(page.ID_LABEL) == "Benchmark ID"
    assert page.get_text(page.ID) == str(TEST_BENCHMARK.id)

    assert page.get_text(page.DESCRIPTION_LABEL) == "Description"
    assert page.get_text(page.DESCRIPTION) == str(TEST_BENCHMARK.description)

    assert page.get_text(page.REF_DATASET_LABEL) == "Reference Dataset Tarball"
    assert page.get_text(page.REF_DATASET) == "Click to Download the File"
    assert (
        page.get_attribute(page.REF_DATASET, "href")
        == TEST_BENCHMARK.demo_dataset_tarball_url
    )
    assert page.get_attribute(page.REF_DATASET, "target") == "_blank"

    assert page.get_text(page.DATA_PREP_LABEL) == "Data Preparation Container"
    assert page.get_text(page.DATA_PREP) == TEST_CONTAINERS[data_prep_cube].name
    assert f"/containers/ui/display/{data_prep_cube}" in page.get_attribute(
        page.DATA_PREP, "href"
    )
    data_prep_date = page.get_attribute(page.DATA_PREP_DATE, "data-date")
    assert parse_ui_date(data_prep_date) == TEST_CONTAINERS[data_prep_cube].modified_at
    data_prep_cls = page.get_attribute(page.DATA_PREP_STATE, "class")
    assert "fa-check-circle" in data_prep_cls and "text-green" in data_prep_cls

    assert page.get_text(page.REF_MODEL_LABEL) == "Reference Model"
    assert page.get_text(page.REF_MODEL) == TEST_CONTAINERS[ref_model_cube].name
    assert f"/models/ui/display/{ref_model_cube}" in page.get_attribute(
        page.REF_MODEL, "href"
    )
    ref_model_date = page.get_attribute(page.REF_MODEL_DATE, "data-date")
    assert parse_ui_date(ref_model_date) == TEST_CONTAINERS[ref_model_cube].modified_at
    ref_model_cls = page.get_attribute(page.REF_MODEL_STATE, "class")
    assert "fa-check-circle" in ref_model_cls and "text-green" in ref_model_cls

    assert page.get_text(page.METRICS_LABEL) == "Metrics Container"
    assert page.get_text(page.METRICS) == TEST_CONTAINERS[metrics_cube].name
    assert f"/containers/ui/display/{metrics_cube}" in page.get_attribute(
        page.METRICS, "href"
    )
    metrics_date = page.get_attribute(page.METRICS_DATE, "data-date")
    assert parse_ui_date(metrics_date) == TEST_CONTAINERS[metrics_cube].modified_at
    metrics_cls = page.get_attribute(page.METRICS_STATE, "class")
    assert "fa-check-circle" in metrics_cls and "text-green" in metrics_cls

    assert page.get_text(page.OWNER_LABEL) == "Owner"
    owner_text = page.get_text(page.OWNER)
    if user == TEST_BENCHMARK.owner:
        assert "You" in owner_text
    else:
        assert str(TEST_BENCHMARK.owner) in owner_text

    assert page.get_text(page.CREATED_LABEL) == "Created"
    bmk_created = page.get_attribute(page.CREATED, "data-date")
    assert parse_ui_date(bmk_created) == TEST_BENCHMARK.created_at

    assert page.get_text(page.MODIFIED_LABEL) == "Modified"
    bmk_modified = page.get_attribute(page.MODIFIED, "data-date")
    assert parse_ui_date(bmk_modified) == TEST_BENCHMARK.modified_at


@pytest.mark.parametrize("user", [TEST_BENCHMARK.owner, TEST_BENCHMARK.owner + 1])
def test_benchmark_details_backend_calls(
    page, mocker, user, patch_bmk_details_empty_assocs_and_results
):
    (
        spy_benchmark,
        spy_datasets_assocs,
        spy_models_assocs,
        spy_results,
        spy_get_datasets_with_users,
        spy_container,
    ) = patch_bmk_details_empty_assocs_and_results

    mocker.patch(PATCH_ROUTE.format("get_medperf_user_data"), return_value={"id": user})

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    if TEST_BENCHMARK.owner == user:
        filters = {"benchmark": TEST_BENCHMARK.id}
        spy_datasets_assocs.assert_called_once_with(benchmark_uid=TEST_BENCHMARK.id)
        spy_models_assocs.assert_called_once_with(benchmark_uid=TEST_BENCHMARK.id)
        spy_results.assert_called_once_with(filters=filters)
        spy_get_datasets_with_users.assert_called_once_with(TEST_BENCHMARK.id)
    else:
        spy_datasets_assocs.assert_not_called()
        spy_models_assocs.assert_not_called()
        spy_results.assert_not_called()
        spy_get_datasets_with_users.assert_not_called()

    spy_benchmark.assert_called_once_with(TEST_BENCHMARK.id)
    assert spy_container.call_count == 2


@pytest.mark.parametrize("user", [TEST_BENCHMARK.owner, TEST_BENCHMARK.owner + 1])
@pytest.mark.parametrize("state", ["OPERATION", "DEVELOPMENT"])
def test_benchmark_details_state(
    page, mocker, user, state, patch_bmk_details_empty_assocs_and_results
):
    TEST_BENCHMARK.state = state

    mocker.patch(PATCH_ROUTE.format("get_medperf_user_data"), return_value={"id": user})

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    if TEST_BENCHMARK.state == "OPERATION":
        assert page.get_text(page.STATE) == "OPERATIONAL"
        assert "text-green-700" in page.get_attribute(page.STATE, "class")
    else:
        assert page.get_text(page.STATE) == TEST_BENCHMARK.state
        assert "text-yellow-700" in page.get_attribute(page.STATE, "class")

    TEST_BENCHMARK.state = "OPERATION"


@pytest.mark.parametrize("user", [TEST_BENCHMARK.owner, TEST_BENCHMARK.owner + 1])
@pytest.mark.parametrize("is_valid", [True, False])
def test_benchmark_details_validity(
    page, mocker, user, is_valid, patch_bmk_details_empty_assocs_and_results
):
    TEST_BENCHMARK.is_valid = is_valid

    mocker.patch(PATCH_ROUTE.format("get_medperf_user_data"), return_value={"id": user})

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    if TEST_BENCHMARK.is_valid:
        assert page.get_text(page.VALID) == "VALID"
        assert "text-green-700" in page.get_attribute(page.VALID, "class")
    else:
        assert page.get_text(page.VALID) == "INVALID"
        assert "text-red-700" in page.get_attribute(page.VALID, "class")

    TEST_BENCHMARK.is_valid = True


@pytest.mark.parametrize("user", [TEST_BENCHMARK.owner, TEST_BENCHMARK.owner + 1])
@pytest.mark.parametrize("docs_url", [None, "http://test.com/docs_url"])
def test_benchmark_details_documentation(
    page, mocker, user, docs_url, patch_bmk_details_empty_assocs_and_results
):
    TEST_BENCHMARK.docs_url = docs_url

    mocker.patch(PATCH_ROUTE.format("get_medperf_user_data"), return_value={"id": user})

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    assert page.get_text(page.DOCUMENTATION_LABEL) == "Documentation"

    if TEST_BENCHMARK.docs_url:
        assert page.get_text(page.DOCUMENTATION) == TEST_BENCHMARK.docs_url
        assert page.get_attribute(page.DOCUMENTATION, "href") == TEST_BENCHMARK.docs_url
        assert page.get_attribute(page.DOCUMENTATION, "target") == "_blank"

        with pytest.raises(NoSuchElementException):
            page.driver.find_element(*page.NO_DOCUMENTATION)
    else:
        assert page.get_text(page.NO_DOCUMENTATION) == "Not Available"

        with pytest.raises(NoSuchElementException):
            page.driver.find_element(*page.DOCUMENTATION)

    TEST_BENCHMARK.docs_url = None


def test_benchmark_details_associations_policy_content_loaded_for_owner(
    page, patch_bmk_details_empty_assocs_and_results, patch_owner
):
    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    page.wait_for_presence_selector(page.POLICY_FORM)

    page.wait_for_presence_selector(page.DATASET_ALLOW_LIST_CONTAINER)
    page.wait_for_presence_selector(page.DATASET_ALLOW_LIST_EMAILS)
    page.wait_for_presence_selector(page.DATASET_ALLOW_LIST)

    page.wait_for_presence_selector(page.MODEL_ALLOW_LIST_CONTAINER)
    page.wait_for_presence_selector(page.MODEL_ALLOW_LIST_EMAILS)
    page.wait_for_presence_selector(page.MODEL_ALLOW_LIST_LABEL)

    assert page.get_text(page.SUB_HEADER_2) == "Association Policy"

    assert page.get_text(page.DATASET_AUTO_APPROVE_LABEL) == "Dataset auto approve mode"
    page.select_by_text(page.DATASET_AUTO_APPROVE, "Allow List")
    assert page.get_text(page.DATASET_ALLOW_LIST_LABEL) == "Allow list emails"

    assert page.get_text(page.MODEL_AUTO_APPROVE_LABEL) == "Model auto approve mode"
    page.select_by_text(page.MODEL_AUTO_APPROVE, "Allow List")
    assert page.get_text(page.MODEL_ALLOW_LIST_LABEL) == "Allow list emails"

    assert "Save Policy" in page.get_text(page.SAVE)


def test_benchmark_details_associations_content_loaded_for_owner(
    page, patch_bmk_details_empty_assocs_and_results, patch_owner
):
    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    page.wait_for_presence_selector(page.DATASETS_ASSOCIATIONS)
    page.wait_for_presence_selector(page.MODELS_ASSOCIATIONS)
    page.wait_for_presence_selector(page.RESULTS)

    dataset_assocs_count = page.get_text(page.DATASETS_ASSOCS_COUNT)
    assert dataset_assocs_count == "0"
    assert (
        page.get_text(page.DATASETS_TITLE).strip(dataset_assocs_count).strip()
        == "Datasets Associations"
    )
    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.DATASETS_PENDING_ASSOCS)

    model_assocs_count = page.get_text(page.MODELS_ASSOCS_COUNT)
    assert model_assocs_count == "0"
    assert (
        page.get_text(page.MODELS_TITLE).strip(model_assocs_count).strip()
        == "Models Associations"
    )
    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.MODELS_PENDING_ASSOCS)

    results_count = page.get_text(page.RESULTS_COUNT)
    assert results_count == "0"
    assert page.get_text(page.RESULTS_TITLE).strip(results_count).strip() == "Results"


def test_benchmark_details_associations_policy_content_not_loaded_for_non_owner(
    page, mocker, patch_bmk_details_empty_assocs_and_results
):
    mocker.patch(
        PATCH_ROUTE.format("get_medperf_user_data"),
        return_value={"id": TEST_BENCHMARK.owner + 1},
    )

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.SUB_HEADER_2)

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.POLICY_FORM)


def test_benchmark_details_associations_content_not_loaded_for_non_owner(
    page, mocker, patch_bmk_details_empty_assocs_and_results
):
    mocker.patch(
        PATCH_ROUTE.format("get_medperf_user_data"),
        return_value={"id": TEST_BENCHMARK.owner + 1},
    )

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.ASSOCIATIONS_RESULTS_CONTAINER)


def test_benchmark_details_page_datasets_associations_content(
    page, patch_bmk_details_assocs_and_results, patch_owner
):
    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    assert (
        page.get_text(page.DATASETS_PENDING_ASSOCS) == "You have pending associations"
    )
    assert page.get_text(page.DATASETS_ASSOCS_COUNT) == str(len(DATASETS_ASSOCS))

    datasets_associations_container = page.find(page.DATASETS_ASSOCIATIONS)
    assert not datasets_associations_container.is_displayed()

    page.click(page.DATASETS_TITLE)
    page.wait_for_visibility_element(datasets_associations_container)
    datasets_associations = page.find_elements(page.DATASETS_ASSOCIATIONS_CARDS)
    assert len(datasets_associations) == len(DATASETS_ASSOCS)

    for assoc in datasets_associations:
        assoc_id = assoc.get_attribute("data-association-id")
        dataset_anchor = assoc.find_element(*page.ASSOC_ANCHOR)
        approval_label = assoc.find_element(*page.ASSOC_APPROVAL_LABEL)
        page.wait_for_visibility_element(approval_label)
        approval = assoc.find_element(*page.ASSOC_APPROVAL).text
        approved_at_label = assoc.find_element(*page.ASSOC_APPROVED_AT_LABEL).text

        approved_at = assoc.find_element(*page.ASSOC_APPROVED_AT)
        modified_at_label = assoc.find_element(*page.ASSOC_MODIFIED_AT_LABEL).text
        modified_at = assoc.find_element(*page.ASSOC_MODIFIED_AT).get_attribute(
            "data-date"
        )
        initiated_by_label = assoc.find_element(*page.ASSOC_INITIATED_BY_LABEL).text
        initiated_by = assoc.find_element(*page.ASSOC_INITIATED_BY).text

        dataset_name = assoc.find_element(*page.ASSOC_NAME).text
        dataset_anchor_name = dataset_anchor.text
        dataset_anchor_url = dataset_anchor.get_attribute("href")

        dataset_id = str(DATASETS_ASSOCS[assoc_id]["dataset"])

        assert dataset_name == dataset_anchor_name == TEST_DATASETS[dataset_id].name
        assert f"/datasets/ui/display/{dataset_id}" in dataset_anchor_url
        assert approval_label.text == "Approval Status:"
        assert approved_at_label == "Approved:"
        assert modified_at_label == "Modified:"
        assert initiated_by_label == "Initiated By:"

        assert approval == DATASETS_ASSOCS[assoc_id]["approval_status"]
        assert modified_at == DATASETS_ASSOCS[assoc_id]["modified_at"]
        assert str(DATASETS_ASSOCS[assoc_id]["initiated_by"]) in initiated_by

        if DATASETS_ASSOCS[assoc_id]["approval_status"] == "APPROVED":
            approved_at_date = approved_at.get_attribute("data-date")
            assert approved_at_date == DATASETS_ASSOCS[assoc_id]["approved_at"]
            with pytest.raises(NoSuchElementException):
                assoc.find_element(*page.ASSOC_REJECT)
            with pytest.raises(NoSuchElementException):
                assoc.find_element(*page.ASSOC_APPROVE)
        elif DATASETS_ASSOCS[assoc_id]["approval_status"] == "REJECTED":
            approved_at_date = approved_at.get_attribute("data-date")
            assert approved_at_date == DATASETS_ASSOCS[assoc_id]["approved_at"]
            assert "invalid-card" in assoc.get_attribute("class")
            with pytest.raises(NoSuchElementException):
                assoc.find_element(*page.ASSOC_REJECT)
            with pytest.raises(NoSuchElementException):
                assoc.find_element(*page.ASSOC_APPROVE)
        else:
            reject_btn = assoc.find_element(*page.ASSOC_REJECT)
            approve_btn = assoc.find_element(*page.ASSOC_APPROVE)

            assert reject_btn.get_attribute("data-dataset-id") == dataset_id
            assert reject_btn.get_attribute("data-benchmark-id") == str(
                TEST_BENCHMARK.id
            )
            assert reject_btn.get_attribute("data-entity-type") == "dataset"
            assert reject_btn.get_attribute("data-action-name") == "reject"

            assert approve_btn.get_attribute("data-dataset-id") == dataset_id
            assert approve_btn.get_attribute("data-benchmark-id") == str(
                TEST_BENCHMARK.id
            )
            assert approve_btn.get_attribute("data-entity-type") == "dataset"
            assert approve_btn.get_attribute("data-action-name") == "approve"

    page.click(page.DATASETS_TITLE)
    page.wait_for_invisibility_element(datasets_associations_container)


def test_benchmark_details_page_models_associations_content(
    page, patch_bmk_details_assocs_and_results, patch_owner
):

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    assert page.get_text(page.MODELS_PENDING_ASSOCS) == "You have pending associations"
    assert page.get_text(page.MODELS_ASSOCS_COUNT) == str(len(MODELS_ASSOCS))

    models_associations_container = page.find(page.MODELS_ASSOCIATIONS)
    assert not models_associations_container.is_displayed()

    page.click(page.MODELS_TITLE)
    page.wait_for_visibility_element(models_associations_container)
    models_associations = page.find_elements(page.MODELS_ASSOCIATIONS_CARDS)
    assert len(models_associations) == len(MODELS_ASSOCS)

    for assoc in models_associations:
        assoc_id = assoc.get_attribute("data-association-id")
        model_anchor = assoc.find_element(*page.ASSOC_ANCHOR)
        approval_label = assoc.find_element(*page.ASSOC_APPROVAL_LABEL)
        page.wait_for_visibility_element(approval_label)
        approval = assoc.find_element(*page.ASSOC_APPROVAL).text
        approved_at_label = assoc.find_element(*page.ASSOC_APPROVED_AT_LABEL).text
        approved_at = assoc.find_element(*page.ASSOC_APPROVED_AT)
        modified_at_label = assoc.find_element(*page.ASSOC_MODIFIED_AT_LABEL).text
        modified_at = assoc.find_element(*page.ASSOC_MODIFIED_AT).get_attribute(
            "data-date"
        )
        initiated_by_label = assoc.find_element(*page.ASSOC_INITIATED_BY_LABEL).text
        initiated_by = assoc.find_element(*page.ASSOC_INITIATED_BY).text

        model_name = assoc.find_element(*page.ASSOC_NAME).text
        model_anchor_name = model_anchor.text
        model_anchor_url = model_anchor.get_attribute("href")

        model_id = str(MODELS_ASSOCS[assoc_id]["model"])

        assert model_name == model_anchor_name == TEST_CONTAINERS[model_id].name
        assert f"/models/ui/display/{model_id}" in model_anchor_url
        assert approval_label.text == "Approval Status:"
        assert approved_at_label == "Approved:"
        assert modified_at_label == "Modified:"
        assert initiated_by_label == "Initiated By:"

        assert approval == MODELS_ASSOCS[assoc_id]["approval_status"]
        assert modified_at == MODELS_ASSOCS[assoc_id]["modified_at"]
        assert str(MODELS_ASSOCS[assoc_id]["initiated_by"]) in initiated_by

        if MODELS_ASSOCS[assoc_id]["approval_status"] == "APPROVED":
            approved_at_date = approved_at.get_attribute("data-date")
            assert approved_at_date == MODELS_ASSOCS[assoc_id]["approved_at"]
            with pytest.raises(NoSuchElementException):
                assoc.find_element(*page.ASSOC_REJECT)
            with pytest.raises(NoSuchElementException):
                assoc.find_element(*page.ASSOC_APPROVE)
        elif MODELS_ASSOCS[assoc_id]["approval_status"] == "REJECTED":
            approved_at_date = approved_at.get_attribute("data-date")
            assert approved_at_date == MODELS_ASSOCS[assoc_id]["approved_at"]
            assert "invalid-card" in assoc.get_attribute("class")
            with pytest.raises(NoSuchElementException):
                assoc.find_element(*page.ASSOC_REJECT)
            with pytest.raises(NoSuchElementException):
                assoc.find_element(*page.ASSOC_APPROVE)
        else:
            reject_btn = assoc.find_element(*page.ASSOC_REJECT)
            approve_btn = assoc.find_element(*page.ASSOC_APPROVE)

            assert reject_btn.get_attribute("data-container-id") == model_id
            assert reject_btn.get_attribute("data-benchmark-id") == str(
                TEST_BENCHMARK.id
            )
            assert reject_btn.get_attribute("data-entity-type") == "model"
            assert reject_btn.get_attribute("data-action-name") == "reject"

            assert approve_btn.get_attribute("data-container-id") == model_id
            assert approve_btn.get_attribute("data-benchmark-id") == str(
                TEST_BENCHMARK.id
            )
            assert approve_btn.get_attribute("data-entity-type") == "model"
            assert approve_btn.get_attribute("data-action-name") == "approve"

    page.click(page.MODELS_TITLE)
    page.wait_for_invisibility_element(models_associations_container)


def test_benchmark_details_page_results_content(
    page, mocker, patch_bmk_details_assocs_and_results, patch_owner
):

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    assert page.get_text(page.RESULTS_COUNT) == str(len(RESULTS))

    results_container = page.find(page.RESULTS)
    assert not results_container.is_displayed()

    page.click(page.RESULTS_TITLE)
    page.wait_for_visibility_element(results_container)
    results = page.find_elements(page.RESULTS_CARDS)
    assert len(results) == len(RESULTS)

    def _json_after_label(paragraph_text: str):
        idx = paragraph_text.find("{")
        if idx == -1:
            idx = paragraph_text.find("[")
        return json.loads(paragraph_text[idx:].strip())

    for result in results:
        result_id = result.get_attribute("data-testid")
        local_result = RESULTS[result_id]
        result_name = result.find_element(*page.RESULT_NAME).text
        result_owner_label = result.find_element(*page.RESULT_OWNER_LABEL).text
        result_owner = result.find_element(*page.RESULT_OWNER).text
        result_model_label = result.find_element(*page.RESULT_MODEL_LABEL).text
        result_model = result.find_element(*page.RESULT_MODEL)
        result_dataset_label = result.find_element(*page.RESULT_DATASET_LABEL).text
        result_dataset = result.find_element(*page.RESULT_DATASET)
        result_inference_label = result.find_element(*page.RESULT_INFERENCE_LABEL).text
        result_inference = result.find_element(*page.RESULT_INFERENCE).text
        result_metrics_label = result.find_element(*page.RESULT_METRICS_LABEL).text
        result_metrics = result.find_element(*page.RESULT_METRICS).text
        result_modified_label = result.find_element(*page.RESULT_MODIFIED_LABEL).text
        result_modified = result.find_element(*page.RESULT_MODIFIED).get_attribute(
            "data-date"
        )

        assert result_name == local_result.name
        assert result_owner_label == "Data Owner:"
        assert result_model_label == "Model:"
        assert result_dataset_label == "Dataset:"
        assert result_inference_label == "Inference Status:"
        assert result_metrics_label == "Metrics Status:"
        assert result_modified_label == "Modified:"

        assert result_model.text == f"ID:{local_result.model}"
        assert (
            f"/containers/ui/display/{local_result.model}"
            in result_model.get_attribute("href")
        )
        assert result_dataset.text == f"ID:{local_result.dataset}"
        assert (
            f"/datasets/ui/display/{local_result.dataset}"
            in result_dataset.get_attribute("href")
        )

        assert (
            DATASETS_WITH_USERS[str(local_result.dataset)]["owner"]["email"]
            in result_owner
        )

        assert _json_after_label(result_inference) == local_result.model_report
        assert _json_after_label(result_metrics) == local_result.evaluation_report

        assert parse_ui_date(result_modified) == local_result.modified_at

        if local_result.finalized:
            result_view_btn = result.find_element(*page.RESULT_VIEW)
            assert "View Result" in result_view_btn.text
            assert (
                json.loads(result_view_btn.get_attribute("data-result"))
                == local_result.results
            )
            with pytest.raises(NoSuchElementException):
                result.find_element(*page.RESULT_NOT_SUBMITTED)
        else:
            assert (
                result.find_element(*page.RESULT_NOT_SUBMITTED).text
                == "Results not submitted"
            )
            with pytest.raises(NoSuchElementException):
                result.find_element(*page.RESULT_VIEW)

    page.click(page.RESULTS_TITLE)
    page.wait_for_invisibility_element(results_container)


@pytest.mark.parametrize(
    "mode", [{"text": "Never", "value": "NEVER"}, {"text": "Always", "value": "ALWAYS"}]
)
def test_benchmark_details_change_dataset_auto_approve_mode_succeed(
    page,
    mocker,
    mode,
    ui,
    patch_common,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_update_policy = mocker.patch(PATCH_ROUTE.format("UpdateAssociationsPolicy.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    model_mode_value = page.get_attribute(page.MODEL_AUTO_APPROVE, "value")

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.select_by_text(page.DATASET_AUTO_APPROVE, mode["text"])
    page.click(page.SAVE)
    page.wait_for_visibility_element(confirm_modal)

    assert "update benchmark associations policy" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Benchmark Associations Policy Successfully Updated"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="update_associations_policy")
    spy_update_policy.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        dataset_mode=mode["value"],
        dataset_emails=None,
        model_mode=model_mode_value,
        model_emails=None,
    )

    spy_event_gen.assert_not_called()

    spy_task_id.assert_not_called()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


@pytest.mark.parametrize(
    "mode", [{"text": "Never", "value": "NEVER"}, {"text": "Always", "value": "ALWAYS"}]
)
def test_benchmark_details_change_dataset_auto_approve_mode_fails(
    page,
    mocker,
    mode,
    ui,
    patch_common,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    error_msg = "Update policy test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_update_policy = mocker.patch(
        PATCH_ROUTE.format("UpdateAssociationsPolicy.run"),
        side_effect=Exception(error_msg),
    )

    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    model_mode_value = page.get_attribute(page.MODEL_AUTO_APPROVE, "value")

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.select_by_text(page.DATASET_AUTO_APPROVE, mode["text"])
    page.click(page.SAVE)
    page.wait_for_visibility_element(confirm_modal)

    assert "update benchmark associations policy" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Failed to Update Benchmark Associations Policy"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="update_associations_policy")
    spy_update_policy.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        dataset_mode=mode["value"],
        dataset_emails=None,
        model_mode=model_mode_value,
        model_emails=None,
    )

    spy_event_gen.assert_not_called()

    spy_task_id.assert_not_called()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


@pytest.mark.parametrize(
    "emails, approve_mode, new_mode",
    [
        ([], "ALLOWLIST", ""),
        (["test@test.com", "test1@test.com"], "ALLOWLIST", ""),
        (["test@test.com", "test1@test.com"], "ALWAYS", "Allow List"),
    ],
)
def test_benchmark_details_dataset_auto_approve_mode_allow_list_emails_loaded(
    page,
    emails,
    approve_mode,
    new_mode,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_BENCHMARK.dataset_auto_approval_allow_list = emails
    TEST_BENCHMARK.dataset_auto_approval_mode = approve_mode

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    assert page.get_attribute(page.DATASET_AUTO_APPROVE, "value") == approve_mode

    if new_mode:
        allow_list_container = page.find(page.DATASET_ALLOW_LIST_CONTAINER)
        allow_list_emails = page.find(page.DATASET_ALLOW_LIST_EMAILS)
        allow_list_label = page.find(page.DATASET_ALLOW_LIST_LABEL)
        allow_list = page.find(page.DATASET_ALLOW_LIST)

        assert not allow_list_container.is_displayed()
        assert not allow_list_emails.is_displayed()
        assert not allow_list_label.is_displayed()
        assert not allow_list.is_displayed()

        page.select_by_text(page.DATASET_AUTO_APPROVE, new_mode)

        assert allow_list_container.is_displayed()
        assert allow_list_emails.is_displayed()
        assert allow_list_label.is_displayed()
        assert allow_list.is_displayed()

    dataset_emails_container = page.find(page.DATASET_ALLOW_LIST_EMAILS)
    dataset_emails = dataset_emails_container.get_attribute("data-allowed-list")

    assert json.loads(dataset_emails) == emails
    emails_chips = dataset_emails_container.find_elements(*page.EMAIL_CHIP)
    assert len(emails_chips) == len(emails)
    for email_chip in emails_chips:
        remove_btn = email_chip.find_element(*page.REMOVE_EMAIL)
        assert email_chip.text.strip(remove_btn.text) in emails


@pytest.mark.parametrize(
    "emails, approve_mode",
    [
        ("test@test.com,", "Allow List"),
        ("test@test.com ", "Allow List"),
        ("test@test.com,test1@test.com,test2@test.com,", "Allow List"),
        ("test@test.com test1@test.com test2@test.com ", "Allow List"),
    ],
)
def test_benchmark_details_dataset_auto_approve_mode_allow_list_emails_input(
    page,
    emails,
    approve_mode,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_BENCHMARK.dataset_auto_approval_allow_list = []
    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    page.select_by_text(page.DATASET_AUTO_APPROVE, approve_mode)
    page.type(page.DATASET_ALLOW_LIST, emails)

    dataset_emails_container = page.find(page.DATASET_ALLOW_LIST_EMAILS)
    emails_chips = dataset_emails_container.find_elements(*page.EMAIL_CHIP)
    emails_parts = emails.split(",") if "," in emails else emails.split(" ")
    emails_list = [i.strip() for i in emails_parts if i.strip()]

    assert len(emails_chips) == len(emails_list)

    for email_chip in emails_chips:
        remove_btn = email_chip.find_element(*page.REMOVE_EMAIL)
        assert email_chip.text.strip(remove_btn.text) in emails
        page.ensure_element_ready(remove_btn)
        remove_btn.click()
    emails_chips = dataset_emails_container.find_elements(*page.EMAIL_CHIP)
    assert len(emails_chips) == 0


@pytest.mark.parametrize(
    "approve_mode, emails",
    [(["Allow List", "ALLOWLIST"], "test@test.com test1@test.com ")],
)
def test_benchmark_details_dataset_auto_approve_mode_allow_list_emails_input_submit(
    page,
    mocker,
    approve_mode,
    emails,
    ui,
    patch_common,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_BENCHMARK.dataset_auto_approval_allow_list = []

    spy_init, spy_reset, spy_notifs = patch_common
    spy_update_policy = mocker.patch(PATCH_ROUTE.format("UpdateAssociationsPolicy.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    model_mode_value = page.get_attribute(page.MODEL_AUTO_APPROVE, "value")

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.select_by_text(page.DATASET_AUTO_APPROVE, approve_mode[0])
    page.type(page.DATASET_ALLOW_LIST, emails)
    page.click(page.SAVE)

    page.wait_for_visibility_element(confirm_modal)

    assert "update benchmark associations policy" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Benchmark Associations Policy Successfully Updated"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="update_associations_policy")
    spy_update_policy.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        dataset_mode=approve_mode[1],
        dataset_emails=emails.strip(),
        model_mode=model_mode_value,
        model_emails=None,
    )

    spy_event_gen.assert_not_called()

    spy_task_id.assert_not_called()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


@pytest.mark.parametrize(
    "mode", [{"text": "Never", "value": "NEVER"}, {"text": "Always", "value": "ALWAYS"}]
)
def test_benchmark_details_change_model_auto_approve_mode_succeed(
    page,
    mocker,
    mode,
    ui,
    patch_common,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_update_policy = mocker.patch(PATCH_ROUTE.format("UpdateAssociationsPolicy.run"))

    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    dataset_mode_value = page.get_attribute(page.DATASET_AUTO_APPROVE, "value")

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.select_by_text(page.MODEL_AUTO_APPROVE, mode["text"])
    page.click(page.SAVE)
    page.wait_for_visibility_element(confirm_modal)

    assert "update benchmark associations policy" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Benchmark Associations Policy Successfully Updated"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="update_associations_policy")
    spy_update_policy.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        dataset_mode=dataset_mode_value,
        dataset_emails=None,
        model_mode=mode["value"],
        model_emails=None,
    )

    spy_event_gen.assert_not_called()

    spy_task_id.assert_not_called()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


@pytest.mark.parametrize(
    "mode", [{"text": "Never", "value": "NEVER"}, {"text": "Always", "value": "ALWAYS"}]
)
def test_benchmark_details_change_model_auto_approve_mode_fails(
    page,
    mocker,
    mode,
    ui,
    patch_common,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    error_msg = "Update policy test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_update_policy = mocker.patch(
        PATCH_ROUTE.format("UpdateAssociationsPolicy.run"),
        side_effect=Exception(error_msg),
    )

    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    dataset_mode_value = page.get_attribute(page.DATASET_AUTO_APPROVE, "value")

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.select_by_text(page.MODEL_AUTO_APPROVE, mode["text"])
    page.click(page.SAVE)
    page.wait_for_visibility_element(confirm_modal)

    assert "update benchmark associations policy" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Failed to Update Benchmark Associations Policy"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="update_associations_policy")
    spy_update_policy.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        dataset_mode=dataset_mode_value,
        dataset_emails=None,
        model_mode=mode["value"],
        model_emails=None,
    )

    spy_event_gen.assert_not_called()

    spy_task_id.assert_not_called()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


@pytest.mark.parametrize(
    "emails, approve_mode, new_mode",
    [
        ([], "ALLOWLIST", ""),
        (["test@test.com", "test1@test.com"], "ALLOWLIST", ""),
        (["test@test.com", "test1@test.com"], "NEVER", "Allow List"),
    ],
)
def test_benchmark_details_model_auto_approve_mode_allow_list_emails_loaded(
    page,
    emails,
    approve_mode,
    new_mode,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_BENCHMARK.model_auto_approval_allow_list = emails
    TEST_BENCHMARK.model_auto_approval_mode = approve_mode

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    assert page.get_attribute(page.MODEL_AUTO_APPROVE, "value") == approve_mode

    if new_mode:
        allow_list_container = page.find(page.MODEL_ALLOW_LIST_CONTAINER)
        allow_list_emails = page.find(page.MODEL_ALLOW_LIST_EMAILS)
        allow_list_label = page.find(page.MODEL_ALLOW_LIST_LABEL)
        allow_list = page.find(page.MODEL_ALLOW_LIST)

        assert not allow_list_container.is_displayed()
        assert not allow_list_emails.is_displayed()
        assert not allow_list_label.is_displayed()
        assert not allow_list.is_displayed()

        page.select_by_text(page.MODEL_AUTO_APPROVE, new_mode)

        assert allow_list_container.is_displayed()
        assert allow_list_emails.is_displayed()
        assert allow_list_label.is_displayed()
        assert allow_list.is_displayed()

    model_emails_container = page.find(page.MODEL_ALLOW_LIST_EMAILS)
    model_emails = model_emails_container.get_attribute("data-allowed-list")

    assert json.loads(model_emails) == emails
    emails_chips = model_emails_container.find_elements(*page.EMAIL_CHIP)
    assert len(emails_chips) == len(emails)
    for email_chip in emails_chips:
        remove_btn = email_chip.find_element(*page.REMOVE_EMAIL)
        assert email_chip.text.strip(remove_btn.text) in emails


@pytest.mark.parametrize(
    "emails, approve_mode",
    [
        ("test@test.com,", "Allow List"),
        ("test@test.com ", "Allow List"),
        ("test@test.com,test1@test.com,test2@test.com,", "Allow List"),
        ("test@test.com test1@test.com test2@test.com ", "Allow List"),
    ],
)
def test_benchmark_details_model_auto_approve_mode_allow_list_emails_input(
    page,
    emails,
    approve_mode,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_BENCHMARK.model_auto_approval_allow_list = []

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    page.select_by_text(page.MODEL_AUTO_APPROVE, approve_mode)
    page.type(page.MODEL_ALLOW_LIST, emails)

    model_emails_container = page.find(page.MODEL_ALLOW_LIST_EMAILS)
    emails_chips = model_emails_container.find_elements(*page.EMAIL_CHIP)
    emails_parts = emails.split(",") if "," in emails else emails.split(" ")
    emails_list = [i.strip() for i in emails_parts if i.strip()]

    assert len(emails_chips) == len(emails_list)

    for email_chip in emails_chips:
        remove_btn = email_chip.find_element(*page.REMOVE_EMAIL)
        assert email_chip.text.strip(remove_btn.text) in emails
        page.ensure_element_ready(remove_btn)
        remove_btn.click()
    emails_chips = model_emails_container.find_elements(*page.EMAIL_CHIP)
    assert len(emails_chips) == 0


@pytest.mark.parametrize(
    "approve_mode, emails",
    [(["Allow List", "ALLOWLIST"], "test@test.com test1@test.com ")],
)
def test_benchmark_details_model_auto_approve_mode_allow_list_emails_input_submit(
    page,
    mocker,
    approve_mode,
    emails,
    ui,
    patch_common,
    patch_bmk_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_BENCHMARK.model_auto_approval_allow_list = []

    spy_init, spy_reset, spy_notifs = patch_common
    spy_update_policy = mocker.patch(PATCH_ROUTE.format("UpdateAssociationsPolicy.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    dataset_mode_value = page.get_attribute(page.DATASET_AUTO_APPROVE, "value")
    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.select_by_text(page.MODEL_AUTO_APPROVE, approve_mode[0])
    page.type(page.MODEL_ALLOW_LIST, emails)
    page.click(page.SAVE)

    page.wait_for_visibility_element(confirm_modal)

    assert "update benchmark associations policy" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Benchmark Associations Policy Successfully Updated"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="update_associations_policy")
    spy_update_policy.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        dataset_mode=dataset_mode_value,
        dataset_emails=None,
        model_mode=approve_mode[1],
        model_emails=emails.strip(),
    )

    spy_event_gen.assert_not_called()

    spy_task_id.assert_not_called()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_reject_dataset_assoc_fails(
    page,
    mocker,
    ui,
    patch_common,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    error_msg = "Dataset association rejection test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_approval = mocker.patch(
        PATCH_ROUTE.format("Approval.run"), side_effect=Exception(error_msg)
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    datasets_associations_container = page.find(page.DATASETS_ASSOCIATIONS)
    page.click(page.DATASETS_TITLE)
    page.wait_for_visibility_element(datasets_associations_container)
    datasets_associations = page.find_elements(page.DATASETS_ASSOCIATIONS_CARDS)

    assoc = [
        assoc
        for assoc in datasets_associations
        if assoc.find_element(*page.ASSOC_APPROVAL).text == "PENDING"
    ][0]

    assoc_id = assoc.get_attribute("data-association-id")
    dataset_id = DATASETS_ASSOCS[assoc_id]["dataset"]

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    reject_btn = assoc.find_element(*page.ASSOC_REJECT)
    page.ensure_element_ready(reject_btn)
    reject_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "reject this association" in page.get_text(page.CONFIRM_TEXT)
    assert "This action cannot be undone" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while rejecting association"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="reject_association")
    spy_approval.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        approval_status=Status.REJECTED,
        dataset_uid=dataset_id,
        model_uid=None,
    )

    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_reject_dataset_assoc_succeed(
    page,
    mocker,
    ui,
    patch_common,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_approval = mocker.patch(PATCH_ROUTE.format("Approval.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    datasets_associations_container = page.find(page.DATASETS_ASSOCIATIONS)
    page.click(page.DATASETS_TITLE)
    page.wait_for_visibility_element(datasets_associations_container)
    datasets_associations = page.find_elements(page.DATASETS_ASSOCIATIONS_CARDS)

    assoc = [
        assoc
        for assoc in datasets_associations
        if assoc.find_element(*page.ASSOC_APPROVAL).text == "PENDING"
    ][0]

    assoc_id = assoc.get_attribute("data-association-id")
    dataset_id = DATASETS_ASSOCS[assoc_id]["dataset"]

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    reject_btn = assoc.find_element(*page.ASSOC_REJECT)
    page.ensure_element_ready(reject_btn)
    reject_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "reject this association" in page.get_text(page.CONFIRM_TEXT)
    assert "This action cannot be undone" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Rejecting association completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="reject_association")
    spy_approval.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        approval_status=Status.REJECTED,
        dataset_uid=dataset_id,
        model_uid=None,
    )

    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_approve_dataset_assoc_fails(
    page,
    mocker,
    ui,
    patch_common,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    error_msg = "Dataset association approval test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_approval = mocker.patch(
        PATCH_ROUTE.format("Approval.run"), side_effect=Exception(error_msg)
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    datasets_associations_container = page.find(page.DATASETS_ASSOCIATIONS)
    page.click(page.DATASETS_TITLE)
    page.wait_for_visibility_element(datasets_associations_container)
    datasets_associations = page.find_elements(page.DATASETS_ASSOCIATIONS_CARDS)

    assoc = [
        assoc
        for assoc in datasets_associations
        if assoc.find_element(*page.ASSOC_APPROVAL).text == "PENDING"
    ][0]

    assoc_id = assoc.get_attribute("data-association-id")
    dataset_id = DATASETS_ASSOCS[assoc_id]["dataset"]

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    approve_btn = assoc.find_element(*page.ASSOC_APPROVE)
    page.ensure_element_ready(approve_btn)
    approve_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "approve this association" in page.get_text(page.CONFIRM_TEXT)
    assert "This action cannot be undone" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while approving association"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="approve_association")
    spy_approval.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        approval_status=Status.APPROVED,
        dataset_uid=dataset_id,
        model_uid=None,
    )

    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_approve_dataset_assoc_succeed(
    page,
    mocker,
    ui,
    patch_common,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_approval = mocker.patch(PATCH_ROUTE.format("Approval.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    datasets_associations_container = page.find(page.DATASETS_ASSOCIATIONS)
    page.click(page.DATASETS_TITLE)
    page.wait_for_visibility_element(datasets_associations_container)
    datasets_associations = page.find_elements(page.DATASETS_ASSOCIATIONS_CARDS)

    assoc = [
        assoc
        for assoc in datasets_associations
        if assoc.find_element(*page.ASSOC_APPROVAL).text == "PENDING"
    ][0]

    assoc_id = assoc.get_attribute("data-association-id")
    dataset_id = DATASETS_ASSOCS[assoc_id]["dataset"]

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    approve_btn = assoc.find_element(*page.ASSOC_APPROVE)
    page.ensure_element_ready(approve_btn)
    approve_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "approve this association" in page.get_text(page.CONFIRM_TEXT)
    assert "This action cannot be undone" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Approving association completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="approve_association")
    spy_approval.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        approval_status=Status.APPROVED,
        dataset_uid=dataset_id,
        model_uid=None,
    )

    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_reject_model_assoc_fails(
    page,
    mocker,
    ui,
    patch_common,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    error_msg = "Model association rejection test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_approval = mocker.patch(
        PATCH_ROUTE.format("Approval.run"), side_effect=Exception(error_msg)
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    models_associations_container = page.find(page.MODELS_ASSOCIATIONS)
    page.click(page.MODELS_TITLE)
    page.wait_for_visibility_element(models_associations_container)
    models_associations = page.find_elements(page.MODELS_ASSOCIATIONS_CARDS)

    assoc = [
        assoc
        for assoc in models_associations
        if assoc.find_element(*page.ASSOC_APPROVAL).text == "PENDING"
    ][0]

    assoc_id = assoc.get_attribute("data-association-id")
    model_id = MODELS_ASSOCS[assoc_id]["model"]

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    reject_btn = assoc.find_element(*page.ASSOC_REJECT)
    page.ensure_element_ready(reject_btn)
    reject_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "reject this association" in page.get_text(page.CONFIRM_TEXT)
    assert "This action cannot be undone" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while rejecting association"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="reject_association")
    spy_approval.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        approval_status=Status.REJECTED,
        dataset_uid=None,
        model_uid=model_id,
    )

    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_rejectmodel_assoc_succeed(
    page,
    mocker,
    ui,
    patch_common,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_approval = mocker.patch(PATCH_ROUTE.format("Approval.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    models_associations_container = page.find(page.MODELS_ASSOCIATIONS)
    page.click(page.MODELS_TITLE)
    page.wait_for_visibility_element(models_associations_container)
    models_associations = page.find_elements(page.MODELS_ASSOCIATIONS_CARDS)

    assoc = [
        assoc
        for assoc in models_associations
        if assoc.find_element(*page.ASSOC_APPROVAL).text == "PENDING"
    ][0]

    assoc_id = assoc.get_attribute("data-association-id")
    model_id = MODELS_ASSOCS[assoc_id]["model"]

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    reject_btn = assoc.find_element(*page.ASSOC_REJECT)
    page.ensure_element_ready(reject_btn)
    reject_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "reject this association" in page.get_text(page.CONFIRM_TEXT)
    assert "This action cannot be undone" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Rejecting association completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="reject_association")
    spy_approval.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        approval_status=Status.REJECTED,
        dataset_uid=None,
        model_uid=model_id,
    )

    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_approve_model_assoc_fails(
    page,
    mocker,
    ui,
    patch_common,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    error_msg = "Model association approval test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_approval = mocker.patch(
        PATCH_ROUTE.format("Approval.run"), side_effect=Exception(error_msg)
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    models_associations_container = page.find(page.MODELS_ASSOCIATIONS)
    page.click(page.MODELS_TITLE)
    page.wait_for_visibility_element(models_associations_container)
    models_associations = page.find_elements(page.MODELS_ASSOCIATIONS_CARDS)

    assoc = [
        assoc
        for assoc in models_associations
        if assoc.find_element(*page.ASSOC_APPROVAL).text == "PENDING"
    ][0]

    assoc_id = assoc.get_attribute("data-association-id")
    model_id = MODELS_ASSOCS[assoc_id]["model"]

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    approve_btn = assoc.find_element(*page.ASSOC_APPROVE)
    page.ensure_element_ready(approve_btn)
    approve_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "approve this association" in page.get_text(page.CONFIRM_TEXT)
    assert "This action cannot be undone" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while approving association"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="approve_association")
    spy_approval.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        approval_status=Status.APPROVED,
        dataset_uid=None,
        model_uid=model_id,
    )

    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_approve_model_assoc_succeed(
    page,
    mocker,
    ui,
    patch_common,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_approval = mocker.patch(PATCH_ROUTE.format("Approval.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    models_associations_container = page.find(page.MODELS_ASSOCIATIONS)
    page.click(page.MODELS_TITLE)
    page.wait_for_visibility_element(models_associations_container)
    models_associations = page.find_elements(page.MODELS_ASSOCIATIONS_CARDS)

    assoc = [
        assoc
        for assoc in models_associations
        if assoc.find_element(*page.ASSOC_APPROVAL).text == "PENDING"
    ][0]

    assoc_id = assoc.get_attribute("data-association-id")
    model_id = MODELS_ASSOCS[assoc_id]["model"]

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    approve_btn = assoc.find_element(*page.ASSOC_APPROVE)
    page.ensure_element_ready(approve_btn)
    approve_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "approve this association" in page.get_text(page.CONFIRM_TEXT)
    assert "This action cannot be undone" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Approving association completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="approve_association")
    spy_approval.assert_called_once_with(
        benchmark_uid=TEST_BENCHMARK.id,
        approval_status=Status.APPROVED,
        dataset_uid=None,
        model_uid=model_id,
    )

    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_benchmark_details_view_results(
    page,
    patch_bmk_details_assocs_and_results,
    patch_owner,
):
    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    page.view_results()


def test_benchmark_details_page_task_running(
    page, patch_bmk_details_assocs_and_results, patch_owner
):
    web_app.state.task_running = True
    web_app.state.task.running = True

    page.open(BASE_URL.format(f"/benchmarks/ui/display/{TEST_BENCHMARK.id}"))

    assert not page.find(page.DATASET_AUTO_APPROVE).is_enabled()
    assert not page.find(page.MODEL_AUTO_APPROVE).is_enabled()
    assert not page.find(page.SAVE).is_enabled()
    assert not page.find(page.DATASET_ALLOW_LIST).is_enabled()
    assert not page.find(page.MODEL_ALLOW_LIST).is_enabled()

    approve_buttons = page.find_elements(page.ASSOC_APPROVE)
    reject_buttons = page.find_elements(page.ASSOC_REJECT)
    assert approve_buttons
    assert reject_buttons
    for btn in approve_buttons + reject_buttons:
        assert not btn.is_enabled()

    view_buttons = page.find_elements(page.RESULT_VIEW)
    assert view_buttons
    for btn in view_buttons:
        assert btn.is_enabled()

    page.driver.find_element(
        By.CSS_SELECTOR, 'script[data-testid="global-event-source-script"]'
    )
