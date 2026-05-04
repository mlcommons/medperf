from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.dataset.details_page import DatasetDetailsPage

import json
import datetime
import pytest
from unittest.mock import ANY, MagicMock
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.cube import TestCube
from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.execution import TestExecution
from medperf.web_ui.app import web_app
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
PATCH_GET_MODEL = "medperf.entities.model.Model.get"
PATCH_DATASET = "medperf.entities.dataset.Dataset.{}"
PATCH_EXECUTION = "medperf.entities.execution.Execution.{}"
PATCH_ROUTE = "medperf.web_ui.datasets.routes.{}"

PATCH_READ_USER_ACCOUNT = "medperf.web_ui.common.read_user_account"
PATCH_GET_MEDPERF_USER_DATA_COMMON = "medperf.web_ui.common.get_medperf_user_data"
PATCH_GET_MEDPERF_USER_DATA_ROUTES = (
    "medperf.web_ui.datasets.routes.get_medperf_user_data"
)
PATCH_GET_MEDPERF_USER_OBJECT = "medperf.web_ui.datasets.routes.get_medperf_user_object"


def _patch_medperf_session(mocker, user_id: int):
    data = {"id": user_id, "email": "dataset-ui-test@local"}
    mocker.patch(PATCH_READ_USER_ACCOUNT, return_value={"email": data["email"]})
    mocker.patch(PATCH_GET_MEDPERF_USER_DATA_COMMON, return_value=data)
    mocker.patch(PATCH_GET_MEDPERF_USER_DATA_ROUTES, return_value=data)
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.is_cc_initialized.return_value = True
    mock_user.get_cc_config.return_value = {}
    mocker.patch(PATCH_GET_MEDPERF_USER_OBJECT, return_value=mock_user)


def _benchmark_id_from_card(card) -> int:
    form = card.find_element(By.CSS_SELECTOR, "form[id^='run-all-']")
    fid = form.get_attribute("id")
    core = fid[len("run-all-"): -len("-form")]
    return int(core)


def _model_id_from_card(model_card) -> str:
    link = model_card.find_element(By.CSS_SELECTOR, "a[href*='/models/ui/display/']")
    return link.get_attribute("href").rstrip("/").split("/")[-1]


DATASET_OWNER = 1
DATASET_ID = 1

DATA_PREP_OWNER = 5

BMK1_OWNER = 10
BMK2_OWNER = 20
BMK3_OWNER = 30

TEST_DATASET = TestDataset(
    id=DATASET_ID,
    owner=DATASET_OWNER,
    name="test_dataset",
    location="test_location",
    description="test description",
    created_at=datetime.datetime(2025, 10, 15),
    modified_at=datetime.datetime(2025, 10, 17),
    state="DEVELOPMENT",
    data_preparation_mlcube=1,
    submitted_as_prepared=False,
    report={},
    generated_metadata={},
)


def __create_benchmark(id, owner, data_prep, ref):
    return TestBenchmark(
        id=id,
        name=f"test_benchmark{id}",
        modified_at=datetime.datetime(2025, 10, id + 10),
        owner=owner,
        data_preparation_mlcube=data_prep,
        reference_model=ref,
    )


def __create_execution(id, approval_status, name, model, finalized):
    finalized_at = datetime.datetime(2025, 10, 17) if finalized else None
    approved_at = (
        datetime.datetime(2025, 10, 17) if approval_status == "APPROVED" else None
    )
    return TestExecution(
        approved_at=approved_at,
        approval_status=approval_status,
        id=id,
        name=name,
        owner=DATASET_OWNER,
        is_valid=True,
        created_at=datetime.datetime(2025, 10, 15),
        modified_at=datetime.datetime(2025, 10, 17),
        benchmark=1,
        model=model,
        dataset=1,
        results={"k1": "v1"},
        model_report={"execution_status": "finished"},
        evaluation_report={"execution_status": "finished"},
        finalized=finalized,
        finalized_at=finalized_at,
    )


def __create_association(id, status, dataset, benchmark, model, initiated_by):
    assoc = {
        "id": id,
        "approval_status": status,
        "approved_at": get_date_string(),
        "created_at": get_date_string(),
        "modified_at": get_date_string(),
        "priority": 0,
        "benchmark": benchmark,
        "initiated_by": initiated_by,
    }

    if dataset:
        assoc["dataset"] = dataset

    if model:
        assoc["model_mlcube"] = model

    return assoc


def __create_container(id, name, owner):
    model_like = TestCube(
        id=id,
        name=name,
        modified_at=datetime.datetime(2025, 10, id + 10),
        owner=owner,
    )
    model_like.requires_cc = lambda: False
    model_like.is_encrypted = lambda: False
    model_like.is_cc_initialized = lambda: True
    model_like.container = model_like
    return model_like


def _generate_test_benchmarks():
    return {
        "1": __create_benchmark(1, BMK1_OWNER, 1, 2),
        "2": __create_benchmark(2, BMK2_OWNER, 1, 3),
        "3": __create_benchmark(3, BMK3_OWNER, 1, 4),
        "4": __create_benchmark(4, 123, 123, 1234),
    }


def _generate_test_executions():
    return {
        "2": __create_execution(1, "PENDING", "b1m2d1", 2, True),
        "3": __create_execution(2, "APPROVED", "b1m3d1", 3, False),
        "5": __create_execution(3, "APPROVED", "b1m5d1", 5, False),
        "6": __create_execution(4, "APPROVED", "b1m6d1", 6, True),
    }


def _generate_test_assocs():
    return {
        "1": __create_association(1, "APPROVED", 1, 1, None, DATASET_OWNER),
        "2": __create_association(2, "REJECTED", 1, 2, None, DATASET_OWNER),
        "3": __create_association(3, "PENDING", 1, 3, None, DATASET_OWNER),
        "4": __create_association(4, "APPROVED", None, 1, 5, 123),
        "5": __create_association(5, "APPROVED", None, 1, 6, 1234),
    }


def _generate_test_containers():
    return {
        "1": __create_container(1, "data-prep", DATA_PREP_OWNER),
        "2": __create_container(2, "ref-model1", BMK1_OWNER),
        "3": __create_container(3, "ref-model2", BMK2_OWNER),
        "4": __create_container(4, "ref-model3", BMK3_OWNER),
        "5": __create_container(5, "model1", 40),
        "6": __create_container(6, "model2", 50),
        "7": __create_container(7, "model3", 60),
        "8": __create_container(8, "model4", 70),
        "9": __create_container(9, "model5", 80),
    }


TEST_CONTAINERS = _generate_test_containers()
TEST_BENCHMARKS = _generate_test_benchmarks()
BENCHMARKS_ASSOCS = _generate_test_assocs()
TEST_EXECUTIONS = _generate_test_executions()


def get_test_container(cube_uid):
    if isinstance(cube_uid, int):
        return TEST_CONTAINERS[str(cube_uid)]
    return TEST_CONTAINERS[str(cube_uid.id)]


def get_test_model(model_uid):
    if isinstance(model_uid, int):
        return TEST_CONTAINERS[str(model_uid)]
    return TEST_CONTAINERS[str(model_uid.id)]


def get_models_assocs(benchmark_uid):
    if benchmark_uid == 1:
        return [5, 6, 7, 8]
    elif benchmark_uid == 2:
        return [5, 7, 9]
    else:
        return [5, 8]


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification

    return (init, reset, notifs)


@pytest.fixture()
def patch_owner(mocker):
    _patch_medperf_session(mocker, DATASET_OWNER)


@pytest.fixture()
def patch_dset_details_empty_assocs_and_results(mocker):
    mocker.patch(PATCH_DATASET.format("get"), return_value=TEST_DATASET)
    mocker.patch(PATCH_DATASET.format("is_ready"), return_value=False)
    mocker.patch(PATCH_DATASET.format("read_report"), return_value=None)
    mocker.patch(PATCH_DATASET.format("read_statistics"), return_value=None)
    mocker.patch(PATCH_GET_CONTAINER, side_effect=get_test_container)
    mocker.patch(PATCH_GET_MODEL, side_effect=get_test_model)
    mocker.patch(
        PATCH_DATASET.format("get_benchmarks_associations"),
        return_value=[],
    )
    mocker.patch(PATCH_BENCHMARK.format("all"), return_value=[])
    mocker.patch(PATCH_EXECUTION.format("all"), return_value=[])
    mocker.patch(
        PATCH_BENCHMARK.format("get_models_uids"), side_effect=get_models_assocs
    )


@pytest.fixture()
def patch_dset_details_assocs_and_results(mocker):
    TEST_CONTAINERS = _generate_test_containers()  # noqa
    TEST_BENCHMARKS = _generate_test_benchmarks()
    BENCHMARKS_ASSOCS = _generate_test_assocs()
    TEST_EXECUTIONS = _generate_test_executions()

    mocker.patch(PATCH_DATASET.format("get"), return_value=TEST_DATASET)
    mocker.patch(PATCH_DATASET.format("is_ready"), return_value=False)
    mocker.patch(PATCH_DATASET.format("read_report"), return_value=None)
    mocker.patch(PATCH_DATASET.format("read_statistics"), return_value=None)
    mocker.patch(PATCH_GET_CONTAINER, side_effect=get_test_container)
    mocker.patch(PATCH_GET_MODEL, side_effect=get_test_model)
    mocker.patch(
        PATCH_DATASET.format("get_benchmarks_associations"),
        return_value=list(BENCHMARKS_ASSOCS.values()),
    )
    mocker.patch(
        PATCH_BENCHMARK.format("all"), return_value=list(TEST_BENCHMARKS.values())
    )
    mocker.patch(
        PATCH_EXECUTION.format("all"), return_value=list(TEST_EXECUTIONS.values())
    )
    mocker.patch(PATCH_EXECUTION.format("read_results"), return_value={"k1": "v1"})
    mocker.patch(
        PATCH_BENCHMARK.format("get_models_uids"), side_effect=get_models_assocs
    )


@pytest.fixture
def page(driver):
    return DatasetDetailsPage(driver, TEST_DATASET.name, "test_benchmark1")


@pytest.mark.parametrize("user", [DATASET_OWNER, DATASET_OWNER + 1])
def test_dataset_details_page_common_content(
    page, mocker, user, patch_dset_details_empty_assocs_and_results, patch_owner
):
    data_prep_cube = str(TEST_DATASET.data_preparation_mlcube)

    _patch_medperf_session(mocker, user)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    assert page.get_text(page.HEADER) == TEST_DATASET.name
    assert page.get_text(page.SUB_HEADER_1) == "Details"

    assert page.get_text(page.ID_LABEL) == "Dataset ID"
    assert page.get_text(page.ID) == str(DATASET_ID)

    assert page.get_text(page.DATA_PREP_LABEL) == "Data Preparation Container"
    assert page.get_text(page.DATA_PREP) == TEST_CONTAINERS[data_prep_cube].name
    assert f"/containers/ui/display/{data_prep_cube}" in page.get_attribute(
        page.DATA_PREP, "href"
    )
    data_prep_date = page.get_attribute(page.DATA_PREP_DATE, "data-date")
    assert parse_ui_date(data_prep_date) == TEST_CONTAINERS[data_prep_cube].modified_at
    assert "fa-check-circle" in page.get_attribute(page.DATA_PREP_STATE, "class")

    assert page.get_text(page.PREPARED_LABEL) == "Is Prepared"
    assert page.get_text(page.PREPARED) == str(TEST_DATASET.is_ready())

    assert page.get_text(page.OWNER_LABEL) == "Owner"
    owner_text = page.get_text(page.OWNER).strip()
    if user == DATASET_OWNER:
        assert owner_text == "You"
    else:
        assert owner_text == str(DATASET_OWNER)

    assert page.get_text(page.CREATED_LABEL) == "Created"

    dataset_created = page.get_attribute(page.CREATED, "data-date")
    assert parse_ui_date(dataset_created) == TEST_DATASET.created_at
    assert page.get_text(page.MODIFIED_LABEL) == "Modified"

    dataset_modified = page.get_attribute(page.MODIFIED, "data-date")
    assert parse_ui_date(dataset_modified) == TEST_DATASET.modified_at


@pytest.mark.parametrize("user", [DATASET_OWNER, DATASET_OWNER + 1])
@pytest.mark.parametrize("state", ["OPERATION", "DEVELOPMENT"])
def test_dataset_details_state(
    page, mocker, user, state, patch_dset_details_empty_assocs_and_results
):
    TEST_DATASET.state = state

    _patch_medperf_session(mocker, user)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    if TEST_DATASET.state == "OPERATION":
        assert page.get_text(page.STATE) == "OPERATIONAL"
        assert "green" in page.get_attribute(page.STATE, "class").lower()
    else:
        assert page.get_text(page.STATE) == TEST_DATASET.state
        assert "yellow" in page.get_attribute(page.STATE, "class").lower()

    TEST_DATASET.state = "DEVELOPMENT"


@pytest.mark.parametrize("user", [DATASET_OWNER, DATASET_OWNER + 1])
@pytest.mark.parametrize("is_valid", [True, False])
def test_dataset_details_validity(
    page, mocker, user, is_valid, patch_dset_details_empty_assocs_and_results
):
    TEST_DATASET.is_valid = is_valid

    _patch_medperf_session(mocker, user)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    if TEST_DATASET.is_valid:
        assert page.get_text(page.VALID) == "VALID"
        assert "green" in page.get_attribute(page.VALID, "class").lower()
    else:
        assert page.get_text(page.VALID) == "INVALID"
        assert "red" in page.get_attribute(page.VALID, "class").lower()

    TEST_DATASET.is_valid = True


@pytest.mark.parametrize("user", [DATASET_OWNER, DATASET_OWNER + 1])
@pytest.mark.parametrize("generated_metadata", [None, {"key1": "value1"}])
def test_dataset_details_statistics(
    page, mocker, user, generated_metadata, patch_dset_details_empty_assocs_and_results
):
    TEST_DATASET.generated_metadata = generated_metadata

    _patch_medperf_session(mocker, user)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    if TEST_DATASET.generated_metadata:
        assert page.get_text(page.STATISTICS_LABEL) == "Statistics"
        statistics_anchor = page.find(page.STATISTICS)
        assert statistics_anchor.get_attribute("data-field") == "Statistics"
        assert statistics_anchor.get_attribute("data-yaml-data") is not None
    else:
        with pytest.raises(NoSuchElementException):
            page.driver.find_element(*page.STATISTICS_LABEL)
        with pytest.raises(NoSuchElementException):
            page.driver.find_element(*page.STATISTICS)

    TEST_DATASET.generated_metadata = {}


@pytest.mark.parametrize("user", [DATASET_OWNER, DATASET_OWNER + 1])
@pytest.mark.parametrize(
    "report, report_path", [(None, ""), ({"key1": "value1"}, "/home/test/test.yaml")]
)
def test_dataset_details_report(
    page, mocker, user, report, report_path, patch_dset_details_empty_assocs_and_results
):
    TEST_DATASET.report = report
    TEST_DATASET.report_path = report_path

    if report:
        mocker.patch(PATCH_ROUTE.format("os.path.exists"), return_value=True)
    else:
        mocker.patch(PATCH_ROUTE.format("os.path.exists"), return_value=False)

    _patch_medperf_session(mocker, user)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    if report:
        assert page.get_text(page.REPORT_LABEL) == "Report"
        report_anchor = page.find(page.REPORT)
        assert report_anchor.get_attribute("data-field") == "Report"
        assert report_anchor.get_attribute("data-yaml-data") is not None
    else:
        with pytest.raises(NoSuchElementException):
            page.driver.find_element(*page.REPORT_LABEL)
        with pytest.raises(NoSuchElementException):
            page.driver.find_element(*page.REPORT)

    TEST_DATASET.report = {}
    TEST_DATASET.report_path = ""


def test_dataset_details_export_form_not_loaded_for_non_owner(
    page, mocker, patch_dset_details_empty_assocs_and_results
):
    _patch_medperf_session(mocker, DATASET_OWNER + 1)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    export_form = page.driver.find_element(*page.EXPORT_FORM)
    assert not export_form.is_displayed()


def test_dataset_details_bottom_buttons_panel_not_loaded_for_non_owner(
    page, mocker, patch_dset_details_empty_assocs_and_results
):
    _patch_medperf_session(mocker, DATASET_OWNER + 1)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.BOTTOM_BUTTONS_CONTAINER)


def test_dataset_details_export_form_loaded_for_owner(
    page, patch_dset_details_empty_assocs_and_results, patch_owner
):
    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    page.wait_for_presence_selector(page.EXPORT_FORM)

    assert page.get_attribute(page.EXPORT, "value") == "Export Dataset"


def test_dataset_details_bottom_buttons_loaded_for_owner(
    page, patch_dset_details_empty_assocs_and_results, patch_owner
):
    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    page.wait_for_presence_selector(page.BOTTOM_BUTTONS_CONTAINER)

    assert (
        page.get_text(page.PERPARE_NOTE)
        == "Run data preprocessing and sanity checks for this dataset."
    )
    assert (
        page.get_text(page.SET_OPERATIONAL_NOTE)
        == "Mark this dataset as operational so it can be used in benchmarks and training experiments."
    )
    assert (
        page.get_text(page.ASSCOATE_NOTE)
        == "Associate this dataset with a benchmark (same data preparation container)"
    )


@pytest.mark.parametrize("state", ["DEVELOPMENT", "OPERATION"])
@pytest.mark.parametrize("prepared", [True, False])
def test_dataset_details_dataset_buttons(
    mocker,
    page,
    state,
    prepared,
    patch_dset_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_DATASET.state = state
    mocker.patch(PATCH_DATASET.format("is_ready"), return_value=prepared)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    if prepared and state == "DEVELOPMENT":
        assert page.get_text(page.PREPARED_TEXT) == "Prepared"
        assert page.get_text(page.SET_OPERATIONAL_BTN) == "Set operational"
        assert (
            page.disabled_associate_title().text.strip() == "Associate with benchmark"
        )

    elif prepared and state == "OPERATION":
        assert page.get_text(page.PREPARED_TEXT) == "Prepared"
        assert page.get_text(page.SET_OPERATIONAL_TEXT) == "Operational"
        assert "Associate with benchmark" in page.get_text(page.DROPDOWN_BTN)

    elif not prepared and state == "DEVELOPMENT":
        assert page.get_text(page.PREPARE_BTN) == "Prepare"
        assert page.disabled_set_operational_title().text.strip() == "Set operational"
        assert (
            page.disabled_associate_title().text.strip() == "Associate with benchmark"
        )

    else:
        assert page.get_text(page.PREPARED_TEXT) == "Prepared"
        assert page.get_text(page.SET_OPERATIONAL_TEXT) == "Operational"
        assert "Associate with benchmark" in page.get_text(page.DROPDOWN_BTN)

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_page_benchmarks_associations_dropdown_content(
    mocker, page, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    mocker.patch(PATCH_DATASET.format("is_ready"), return_value=True)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    associable_benchmarks_count = 0
    associations = [a["benchmark"] for a in BENCHMARKS_ASSOCS.values()]
    for benchmark in TEST_BENCHMARKS.values():
        benchmark_id = benchmark.id
        if benchmark.data_preparation_mlcube == 1 and (
            benchmark.id not in associations
            or benchmark.id
            in [
                a["benchmark"]
                for a in BENCHMARKS_ASSOCS.values()
                if a["approval_status"] == "REJECTED"
            ]
        ):
            associable_benchmarks_count += 1

    dropdown_container = page.find(page.DROPDOWN_CONTAINER)
    page.click(page.DROPDOWN_BTN)
    page.wait_for_visibility_element(dropdown_container)
    associations_items = dropdown_container.find_elements(
        By.CSS_SELECTOR, ":scope > div"
    )

    assert len(associations_items) == associable_benchmarks_count

    for item in associations_items:
        bmk_data = item.find_element(*page.BMK_DATA).text
        bmk_view = item.find_element(*page.BMK_VIEW)
        bmk_associate = item.find_element(*page.BMK_ASSOCIATE)

        benchmark_id = item.find_element(
            By.CSS_SELECTOR, "input[name='benchmark_id']"
        ).get_attribute("value")
        dataset_id = item.find_element(
            By.CSS_SELECTOR, "input[name='entity_id']"
        ).get_attribute("value")

        assert bmk_data == f"{benchmark_id} - {TEST_BENCHMARKS[str(benchmark_id)].name}"
        assert f"/benchmarks/ui/display/{benchmark_id}" in bmk_view.get_attribute(
            "href"
        )
        assert bmk_view.text.strip() == "View"
        assert "Request" in bmk_associate.text
        assert dataset_id == str(DATASET_ID)

    with pytest.raises(NoSuchElementException):
        dropdown_container.find_element(*page.NO_BMKS)

    TEST_DATASET.submitted_as_prepared = False
    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_page_prepare_fails(
    page,
    mocker,
    ui,
    patch_common,
    patch_dset_details_empty_assocs_and_results,
    patch_owner,
):
    error_msg = "Dataset preparation test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_prepare = mocker.patch(
        PATCH_ROUTE.format("DataPreparation.run"),
        side_effect=Exception(error_msg),
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.prepare_dataset()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while preparing dataset"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="prepare")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_prepare.assert_called_once_with(DATASET_ID)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_dataset_details_page_prepare_succeed(
    page,
    mocker,
    ui,
    patch_common,
    patch_dset_details_empty_assocs_and_results,
    patch_owner,
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_prepare = mocker.patch(
        PATCH_ROUTE.format("DataPreparation.run"),
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.prepare_dataset()

    page.wait_for_visibility_element(confirm_modal)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Preparing dataset completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="prepare")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_prepare.assert_called_once_with(DATASET_ID)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_dataset_details_set_opreational_fails(
    page,
    mocker,
    ui,
    patch_common,
    patch_dset_details_empty_assocs_and_results,
    patch_owner,
):
    error_msg = "Dataset set operational test failed"
    TEST_DATASET.submitted_as_prepared = True
    mocker.patch(PATCH_DATASET.format("is_ready"), return_value=True)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_set_operational = mocker.patch(
        PATCH_ROUTE.format("DatasetSetOperational.run"),
        side_effect=Exception(error_msg),
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.set_operational()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while setting dataset to operational"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="dataset_set_operational")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_set_operational.assert_called_once_with(DATASET_ID)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.submitted_as_prepared = False


def test_dataset_details_set_opreational_succeed(
    page,
    mocker,
    ui,
    patch_common,
    patch_dset_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_DATASET.submitted_as_prepared = True
    mocker.patch(PATCH_DATASET.format("is_ready"), return_value=True)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_set_operational = mocker.patch(
        PATCH_ROUTE.format("DatasetSetOperational.run"),
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.set_operational()

    page.wait_for_visibility_element(confirm_modal)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Setting dataset to operational completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="dataset_set_operational")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_set_operational.assert_called_once_with(DATASET_ID)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.submitted_as_prepared = False


def test_dataset_details_request_association_fails(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    error_msg = "Request association test failed"
    TEST_DATASET.state = "OPERATION"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_request_assoc = mocker.patch(
        PATCH_ROUTE.format("AssociateDataset.run"), side_effect=Exception(error_msg)
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    dropdown_container = page.find(page.DROPDOWN_CONTAINER)
    page.click(page.DROPDOWN_BTN)
    page.wait_for_visibility_element(dropdown_container)
    associations_items = dropdown_container.find_elements(
        By.CSS_SELECTOR, ":scope > div"
    )
    bmk_associate = associations_items[0].find_element(*page.BMK_ASSOCIATE)

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.ensure_element_ready(bmk_associate)
    bmk_associate.click()
    page.wait_for_visibility_element(confirm_modal)

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while requesting association"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="dataset_association")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_request_assoc.assert_called_once_with(data_uid=DATASET_ID, benchmark_uid=2)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_request_association_success(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_request_assoc = mocker.patch(PATCH_ROUTE.format("AssociateDataset.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    dropdown_container = page.find(page.DROPDOWN_CONTAINER)
    page.click(page.DROPDOWN_BTN)
    page.wait_for_visibility_element(dropdown_container)
    associations_items = dropdown_container.find_elements(
        By.CSS_SELECTOR, ":scope > div"
    )
    bmk_associate = associations_items[0].find_element(*page.BMK_ASSOCIATE)

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.ensure_element_ready(bmk_associate)
    bmk_associate.click()
    page.wait_for_visibility_element(confirm_modal)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Requesting association completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="dataset_association")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_request_assoc.assert_called_once_with(data_uid=DATASET_ID, benchmark_uid=2)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_associations_not_loaded_for_non_owner(
    page, mocker, patch_dset_details_assocs_and_results
):
    _patch_medperf_session(mocker, DATASET_OWNER + 1)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.ASSOCIATIONS_CONTAINER)


def test_dataset_details_non_approved_associations_content(
    page, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    dataset_benchmarks = [
        i
        for i, assoc in BENCHMARKS_ASSOCS.items()
        if assoc.get("dataset") == DATASET_ID
    ]

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    associations = page.find_elements(page.BMKS_ASSOCIATIONS)
    for assoc in associations:
        id_span = assoc.find_element(By.XPATH, ".//span[contains(.,'ID:')]")
        bmk_id = int(id_span.text.replace("ID:", "").strip())
        assoc_bmk = assoc.find_element(By.TAG_NAME, "a")
        status_el = assoc.find_elements(
            By.XPATH, ".//span[contains(@class,'rounded-full')]"
        )[-1]
        assoc_status = status_el.text

        assert str(bmk_id) in dataset_benchmarks
        assert assoc_bmk.text == TEST_BENCHMARKS[str(bmk_id)].name
        assert (
            f"/benchmarks/ui/display/{TEST_BENCHMARKS[str(bmk_id)].id}"
            in assoc_bmk.get_attribute("href")
        )
        assert assoc_status == BENCHMARKS_ASSOCS[str(bmk_id)]["approval_status"]

        if assoc_status == "REJECTED":
            assert "red" in status_el.get_attribute("class").lower()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_all_associations_rendered(
    page, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    approved_benchmarks = 0
    associations = [i for i in BENCHMARKS_ASSOCS.values() if "dataset" in i]
    for assoc in associations:
        if assoc["approval_status"] == "APPROVED" and assoc["dataset"] == DATASET_ID:
            approved_benchmarks += 1

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    page.wait_for_presence_selector(page.ASSOCIATIONS_CONTAINER)

    assert page.get_text(page.ASSOCIATIONS_TITLE) == "Associated benchmarks"
    dataset_assocs = [a for a in associations if a.get("dataset") == DATASET_ID]
    assert len(page.find_elements(page.BMKS_ASSOCIATIONS)) == len(dataset_assocs)

    assert len(page.find_elements(page.APPROVED_BMKS)) == approved_benchmarks

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_approved_associations_ref_model(
    page, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    approved_benchmarks = [
        i
        for i in BENCHMARKS_ASSOCS
        if BENCHMARKS_ASSOCS[i]["approval_status"] == "APPROVED"
    ]

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    approved_bmks = page.find_elements(page.APPROVED_BMKS)

    for bmk in approved_bmks:
        bmk_id = str(_benchmark_id_from_card(bmk))
        ref_model_cube = str(TEST_BENCHMARKS[bmk_id].reference_model)
        label = bmk.find_element(*page.BMK_LABEL)
        name = bmk.find_element(*page.BMK_NAME)
        run_all_btn = bmk.find_element(*page.BMK_RUN_ALL)
        ref_model_label = bmk.find_element(*page.REF_MODEL_LABEL)
        ref_model = bmk.find_element(*page.REF_MODEL)
        ref_model_date = bmk.find_element(*page.REF_MODEL_DATE).get_attribute(
            "data-date"
        )
        ref_model_state = bmk.find_element(*page.REF_MODEL_STATE)
        ref_model_card = bmk.find_element(*page.REF_MODEL_CARD)

        run_btn = ref_model_card.find_element(*page.RUN_MODEL_BTN)
        view_btn = ref_model_card.find_element(*page.VIEW_RESULT_BTN)

        assert bmk_id in approved_benchmarks

        assert "Benchmark:" in label.text
        assert name.text == TEST_BENCHMARKS[bmk_id].name
        assert (
            f"/benchmarks/ui/display/{TEST_BENCHMARKS[bmk_id].id}"
            in name.get_attribute("href")
        )
        assert "Run All" in run_all_btn.text

        assert ref_model_label.text.strip() == "Reference Model"
        assert ref_model.text == TEST_CONTAINERS[ref_model_cube].name
        assert f"/models/ui/display/{ref_model_cube}" in ref_model.get_attribute("href")
        assert (
            parse_ui_date(ref_model_date) == TEST_CONTAINERS[ref_model_cube].modified_at
        )
        assert "fa-check-circle" in ref_model_state.get_attribute("class")

        assert "Rerun" in run_btn.text
        assert "View Result" in view_btn.text

        assert (
            json.loads(view_btn.get_attribute("data-result"))
            == TEST_EXECUTIONS[ref_model_cube].results
        )
        if TEST_EXECUTIONS[ref_model_cube].finalized:
            assert "Submitted" in ref_model_card.find_element(*page.SUBMITTED_TEXT).text

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_approved_associations_models(
    page, mocker, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    approved_benchmarks = [
        i
        for i in BENCHMARKS_ASSOCS
        if BENCHMARKS_ASSOCS[i]["approval_status"] == "APPROVED"
    ]
    mocker.patch(PATCH_EXECUTION.format("is_executed"), return_value=True)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    approved_bmks = page.find_elements(page.APPROVED_BMKS)

    for bmk in approved_bmks:
        bmk_id = str(_benchmark_id_from_card(bmk))
        label = bmk.find_element(*page.BMK_LABEL)
        name = bmk.find_element(*page.BMK_NAME)
        run_all_btn = bmk.find_element(*page.BMK_RUN_ALL)
        model_card = bmk.find_element(*page.MODEL_CARD)
        model = model_card.find_element(*page.MODEL)
        model_date = model_card.find_element(*page.MODEL_DATE).get_attribute(
            "data-date"
        )
        model_state = model_card.find_element(*page.MODEL_STATE)

        model_id = _model_id_from_card(model_card)
        run_btn = model_card.find_element(*page.RUN_MODEL_BTN)

        assert bmk_id in approved_benchmarks

        assert "Benchmark:" in label.text
        assert name.text == TEST_BENCHMARKS[bmk_id].name
        assert (
            f"/benchmarks/ui/display/{TEST_BENCHMARKS[bmk_id].id}"
            in name.get_attribute("href")
        )
        assert "Run All" in run_all_btn.text

        assert model.text == TEST_CONTAINERS[model_id].name
        assert f"/models/ui/display/{model_id}" in model.get_attribute("href")
        assert parse_ui_date(model_date) == TEST_CONTAINERS[model_id].modified_at
        assert "fa-check-circle" in model_state.get_attribute("class")

        if model_id in TEST_EXECUTIONS and TEST_EXECUTIONS[model_id].results:
            view_btn = model_card.find_element(*page.VIEW_RESULT_BTN)

            assert "Rerun" in run_btn.text
            assert "View Result" in view_btn.text
            assert (
                json.loads(view_btn.get_attribute("data-result"))
                == TEST_EXECUTIONS[model_id].results
            )

            if TEST_EXECUTIONS[model_id].finalized:
                assert "Submitted" in model_card.find_element(*page.SUBMITTED_TEXT).text
            else:
                assert "Submit" in model_card.find_element(*page.SUBMIT_BTN).text
        else:
            assert "Run" in run_btn.text
            for selector in [
                page.VIEW_RESULT_BTN,
                page.SUBMIT_BTN,
                page.SUBMITTED_TEXT,
            ]:
                with pytest.raises(NoSuchElementException):
                    model_card.find_element(*selector)

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_run_execution_fails(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"
    error_msg = "Execution run test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_run_execution = mocker.patch(
        PATCH_ROUTE.format("BenchmarkExecution.run"),
        side_effect=Exception(error_msg),
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    approved_bmk = page.find_elements(page.APPROVED_BMKS)[0]
    bmk_id = _benchmark_id_from_card(approved_bmk)
    run_btn = approved_bmk.find_element(*page.BMK_RUN_ALL)
    page.ensure_element_ready(run_btn)
    run_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "run the benchmark execution for all models?" in page.get_text(
        page.CONFIRM_TEXT
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while running benchmark execution"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="run_benchmark")
    spy_run_execution.assert_called_once_with(
        bmk_id,
        DATASET_ID,
        [TEST_BENCHMARKS[str(bmk_id)].reference_model] + get_models_assocs(bmk_id),
        no_cache=False,
        rerun_finalized_executions=False,
    )
    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_run_execution_succeed(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_run_execution = mocker.patch(PATCH_ROUTE.format("BenchmarkExecution.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    approved_bmk = page.find_elements(page.APPROVED_BMKS)[0]
    bmk_id = _benchmark_id_from_card(approved_bmk)
    run_btn = approved_bmk.find_element(*page.BMK_RUN_ALL)
    page.ensure_element_ready(run_btn)
    run_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "run the benchmark execution for all models?" in page.get_text(
        page.CONFIRM_TEXT
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Running benchmark execution completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="run_benchmark")
    spy_run_execution.assert_called_once_with(
        bmk_id,
        DATASET_ID,
        [TEST_BENCHMARKS[str(bmk_id)].reference_model] + get_models_assocs(bmk_id),
        no_cache=False,
        rerun_finalized_executions=False,
    )
    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_view_result(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    page.view_results()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_submit_result_fails(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"
    error_msg = "Results submission test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_results_submit = mocker.patch(
        PATCH_ROUTE.format("ResultSubmission.run"),
        side_effect=Exception(error_msg),
    )
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_EXECUTION.format("is_executed"), return_value=True)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    approved_bmk = page.find_elements(page.APPROVED_BMKS)[0]
    models = approved_bmk.find_elements(*page.MODEL_CARD)

    submit_btn = None
    model_id = None
    for model in models:
        mid = _model_id_from_card(model)
        if mid in TEST_EXECUTIONS and not TEST_EXECUTIONS[mid].finalized:
            submit_btn = model.find_element(*page.SUBMIT_BTN)
            model_id = mid
            break

    assert submit_btn is not None

    page.ensure_element_ready(submit_btn)
    submit_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while submitting result"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="submit_result")
    spy_results_submit.assert_called_once_with(str(TEST_EXECUTIONS[model_id].id))
    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_submit_result_success(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_results_submit = mocker.patch(PATCH_ROUTE.format("ResultSubmission.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_EXECUTION.format("is_executed"), return_value=True)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    approved_bmk = page.find_elements(page.APPROVED_BMKS)[0]
    models = approved_bmk.find_elements(*page.MODEL_CARD)

    submit_btn = None
    model_id = None
    for model in models:
        mid = _model_id_from_card(model)
        if mid in TEST_EXECUTIONS and not TEST_EXECUTIONS[mid].finalized:
            submit_btn = model.find_element(*page.SUBMIT_BTN)
            model_id = mid
            break

    assert submit_btn is not None

    page.ensure_element_ready(submit_btn)
    submit_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Submitting result completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="submit_result")
    spy_results_submit.assert_called_once_with(str(TEST_EXECUTIONS[model_id].id))
    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_run_single_model_backend_call(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_run_execution = mocker.patch(PATCH_ROUTE.format("BenchmarkExecution.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    approved_bmk = page.find_elements(page.APPROVED_BMKS)[0]
    bmk_id = _benchmark_id_from_card(approved_bmk)
    models = approved_bmk.find_elements(*page.MODEL_CARD)

    run_btn = None
    model_id = None
    for model in models:
        mid = _model_id_from_card(model)
        if mid not in TEST_EXECUTIONS:
            run_btn = model.find_element(*page.RUN_MODEL_BTN)
            model_id = mid
            break

    assert run_btn is not None

    page.ensure_element_ready(run_btn)
    run_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert "run the benchmark execution for the selected model?" in page.get_text(
        page.CONFIRM_TEXT
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Running benchmark execution completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="run_benchmark")
    spy_run_execution.assert_called_once_with(
        bmk_id,
        DATASET_ID,
        [int(model_id)],
        no_cache=True,
        rerun_finalized_executions=True,
    )
    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_model_submitted_results_rerun(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_run_execution = mocker.patch(PATCH_ROUTE.format("BenchmarkExecution.run"))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_EXECUTION.format("is_executed"), return_value=True)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    approved_bmk = page.find_elements(page.APPROVED_BMKS)[0]
    bmk_id = _benchmark_id_from_card(approved_bmk)
    models = approved_bmk.find_elements(*page.MODEL_CARD)

    run_btn = None
    model_id = None
    for model in models:
        mid = _model_id_from_card(model)
        if mid in TEST_EXECUTIONS and TEST_EXECUTIONS[mid].finalized:
            run_btn = model.find_element(*page.RUN_MODEL_BTN)
            model_id = mid
            break

    assert run_btn is not None

    page.ensure_element_ready(run_btn)
    run_btn.click()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        "rerun the benchmark execution for the selected model? This will clear previous results."
        in page.get_text(page.CONFIRM_TEXT)
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Running benchmark execution completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="run_benchmark")
    spy_run_execution.assert_called_once_with(
        bmk_id,
        DATASET_ID,
        [int(model_id)],
        no_cache=True,
        rerun_finalized_executions=True,
    )
    spy_event_gen.assert_called_once_with(ANY, False)

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_task_running_resume_prepare(
    page,
    mocker,
    ui,
    patch_common,
    patch_dset_details_empty_assocs_and_results,
    patch_owner,
):
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "prepare"
    web_app.state.task.formData = {"entity_id": str(DATASET_ID)}

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    prepare_btn = page.find(page.PREPARE_BTN)

    assert not prepare_btn.is_enabled()
    assert page.element_contains_spinner(prepare_btn)

    page.find(page.RESUME_SCRIPT_PREPARE)

    spy_event_gen.assert_called_once_with(ANY, True)


def test_dataset_details_task_running_resume_set_operational(
    page,
    mocker,
    ui,
    patch_common,
    patch_dset_details_empty_assocs_and_results,
    patch_owner,
):
    TEST_DATASET.submitted_as_prepared = True
    mocker.patch(PATCH_DATASET.format("is_ready"), return_value=True)

    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "dataset_set_operational"
    web_app.state.task.formData = {"entity_id": str(DATASET_ID)}

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    set_operational_btn = page.find(page.SET_OPERATIONAL_BTN)

    assert not set_operational_btn.is_enabled()
    assert page.element_contains_spinner(set_operational_btn)

    page.find(page.RESUME_SCRIPT_SET_OPERATIONAL)

    spy_event_gen.assert_called_once_with(ANY, True)

    TEST_DATASET.submitted_as_prepared = False


def test_dataset_details_task_running_resume_association(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "dataset_association"
    web_app.state.task.formData = {
        "entity_id": str(DATASET_ID),
        "benchmark_id": "1",
    }

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    associate_dropdown = page.find(page.DROPDOWN_BTN)

    assert not associate_dropdown.is_enabled()

    page.find(page.RESUME_SCRIPT_ASSOCIATE)

    spy_event_gen.assert_called_once_with(ANY, True)

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_task_running_resume_execution_all(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "run_benchmark"
    web_app.state.task.formData = {
        "entity_id": str(DATASET_ID),
        "benchmark_id": "1",
        "model_ids": ["2", "3", "4"],
        "run_all": "true",
    }

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    benchmark_association = next(
        i
        for i in page.find_elements(page.APPROVED_BMKS)
        if _benchmark_id_from_card(i) == 1
    )

    run_all_btn = benchmark_association.find_element(*page.BMK_RUN_ALL)

    assert not run_all_btn.is_enabled()

    model_cards = benchmark_association.find_elements(*page.MODEL_CARD)
    model_cards.append(benchmark_association.find_element(*page.REF_MODEL_CARD))

    for model in model_cards:
        run_btn = model.find_element(*page.RUN_MODEL_BTN)
        assert not run_btn.is_enabled()

    page.find(page.RESUME_SCRIPT_RUN_EXECUTION)

    spy_event_gen.assert_called_once_with(ANY, True)

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_task_running_resume_execution_one(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "run_benchmark"
    web_app.state.task.formData = {
        "entity_id": str(DATASET_ID),
        "benchmark_id": "1",
        "model_ids": "5",
        "run_all": "false",
    }

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    benchmark_association = next(
        i
        for i in page.find_elements(page.APPROVED_BMKS)
        if _benchmark_id_from_card(i) == 1
    )

    run_all_btn = benchmark_association.find_element(*page.BMK_RUN_ALL)

    assert not run_all_btn.is_enabled()
    assert not page.element_contains_spinner(run_all_btn)

    model_cards = benchmark_association.find_elements(*page.MODEL_CARD)
    model_cards.append(benchmark_association.find_element(*page.REF_MODEL_CARD))

    for model in model_cards:
        run_btn = model.find_element(*page.RUN_MODEL_BTN)

        assert not run_btn.is_enabled()

        if _model_id_from_card(model) == "5":
            assert page.element_contains_spinner(run_btn)
        else:
            assert not page.element_contains_spinner(run_btn)

    page.find(page.RESUME_SCRIPT_RUN_EXECUTION)

    spy_event_gen.assert_called_once_with(ANY, True)

    TEST_DATASET.state = "DEVELOPMENT"


def test_dataset_details_task_running_resume_result_submission(
    page, mocker, ui, patch_common, patch_dset_details_assocs_and_results, patch_owner
):
    TEST_DATASET.state = "OPERATION"

    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "submit_result"
    web_app.state.task.formData = {
        "entity_id": str(DATASET_ID),
        "benchmark_id": "1",
        "result_id": "3",
    }

    mocker.patch(PATCH_EXECUTION.format("is_executed"), return_value=True)

    page.open(BASE_URL.format(f"/datasets/ui/display/{DATASET_ID}"))

    submit_btn = page.driver.find_element(By.ID, "submit-1-3")
    assert not submit_btn.is_enabled()
    assert page.element_contains_spinner(submit_btn)

    page.find(page.RESUME_SCRIPT_SUBMIT_RESULT)

    spy_event_gen.assert_called_once_with(ANY, True)

    TEST_DATASET.state = "DEVELOPMENT"
