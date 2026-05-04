import datetime

from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.benchmark.register_page import RegBenchmarkPage

import pytest
from unittest.mock import ANY
from medperf.tests.mocks.cube import TestCube
import medperf.web_ui.events as events_module
from medperf.web_ui.app import web_app
from selenium.common.exceptions import NoSuchElementException

from medperf.web_ui.tests.unit.helpers import stub_event_generator


BASE_URL = tests_config.BASE_URL
PATCH_GET_CONTAINERS = "medperf.entities.cube.Cube.all"
PATCH_GET_MODELS = "medperf.entities.model.Model.all"
PATCH_GET_CONTAINERS_TYPE = "medperf.web_ui.benchmarks.routes.get_container_type"
PATCH_REGISTER = "medperf.commands.benchmark.submit.SubmitBenchmark.run"
PATCH_ROUTE = "medperf.web_ui.benchmarks.routes.{}"

TEST_CONTAINERS = [
    TestCube(id="1", name="data-prep"),
    TestCube(id="3", name="metrics"),
]

TEST_MODELS = [
    TestCube(id="4", name="model-1"),
    TestCube(id="2", name="ref-model"),
]

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


def fake_container_type(container: TestCube):
    if container.name == "data-prep":
        return "data-prep-container"
    elif container.name == "ref-model":
        return "reference-container"
    return "metrics-container"


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification

    return (init, reset, notifs)


@pytest.fixture(autouse=True)
def patch_login(mocker):
    mocker.patch(
        "medperf.web_ui.benchmarks.routes.get_medperf_user_data",
        return_value={"id": 99, "email": "test@example.com"},
    )


@pytest.fixture
def page(driver):
    return RegBenchmarkPage(driver)


def test_benchmark_registration_page_content(page, mocker):
    mocker.patch(PATCH_GET_CONTAINERS, return_value=[])
    mocker.patch(PATCH_GET_MODELS, return_value=[])

    page.open(BASE_URL.format("/benchmarks/register/ui"))

    page.wait_for_presence_selector(page.FORM)

    page.wait_for_presence_selector(page.NAME)
    page.wait_for_presence_selector(page.NAME_TOOLTIP)

    page.wait_for_presence_selector(page.DESCRIPTION)
    page.wait_for_presence_selector(page.DESCRIPTION_TOOLTIP)

    page.wait_for_presence_selector(page.REF_DATASET)
    page.wait_for_presence_selector(page.REF_DATASET_TOOLTIP)

    page.wait_for_presence_selector(page.ALREADY_PREPARED)

    page.wait_for_presence_selector(page.NOT_PREPARED)

    page.wait_for_presence_selector(page.DATA_PREP)

    page.wait_for_presence_selector(page.REF_MODEL)

    page.wait_for_presence_selector(page.METRICS)

    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.TEXT_CONTAINER)
    page.wait_for_presence_selector(page.PROMPT_CONTAINER)

    assert page.get_text(page.HEADER) == "Register a New Benchmark"
    assert page.get_text(page.NAME_LABEL) == "Benchmark Name"
    assert page.get_text(page.DESCRIPTION_LABEL) == "Description"
    assert page.get_text(page.REF_DATASET_LABEL) == "Reference Dataset Tarball URL"
    assert page.get_text(page.ALREADY_PREPARED_LABEL).strip() == "Already Prepared"
    assert page.get_text(page.NOT_PREPARED_LABEL).strip() == "Not Prepared"
    assert page.get_text(page.DATA_PREP_LABEL) == "Data Preparation Container"
    assert page.get_text(page.REF_MODEL_LABEL) == "Reference Model"
    assert page.get_text(page.METRICS_LABEL) == "Metrics Container"
    assert page.get_text(page.REGISTER) == "Register Benchmark"


def test_benchmark_registration_page_tooltips(page, mocker):
    mocker.patch(PATCH_GET_CONTAINERS, return_value=TEST_CONTAINERS)
    mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=fake_container_type)
    mocker.patch(PATCH_GET_MODELS, return_value=TEST_MODELS)

    page.open(BASE_URL.format("/benchmarks/register/ui"))

    name_tooltip = page.find(page.NAME_TOOLTIP)
    description_tooltip = page.find(page.DESCRIPTION_TOOLTIP)
    ref_dataset_tooltip = page.find(page.REF_DATASET_TOOLTIP)

    assert (
        name_tooltip.get_attribute("title")
        == "Name of the benchmark you are registering"
    )
    assert description_tooltip.get_attribute("title") == (
        "Description of the benchmark you are registering"
    )
    assert ref_dataset_tooltip.get_attribute("title") == (
        "Full URL of the reference dataset tarball"
    )


def test_benchmark_registration_fails(page, mocker, ui, patch_common):
    error_message = "Benchmark registration test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_containers = mocker.patch(PATCH_GET_CONTAINERS, return_value=TEST_CONTAINERS)
    spy_type = mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=fake_container_type)
    spy_models = mocker.patch(PATCH_GET_MODELS, return_value=TEST_MODELS)
    spy_register = mocker.patch(PATCH_REGISTER, side_effect=Exception(error_message))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format("/benchmarks/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.click(page.NOT_PREPARED)
    page.click(page.REQUIRE_TESTS)
    import time

    time.sleep(1)
    page.register_benchmark(
        name="test_benchmark",
        description="test description",
        reference_dataset="https://test.com/test.tar.gz",
        data_preparator="data-prep",
        reference_model="ref-model",
        metrics="metrics",
    )

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while registering benchmark"
    )
    assert error_message in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    bmk_info = {
        "name": "test_benchmark",
        "description": "test description",
        "demo_dataset_tarball_url": "https://test.com/test.tar.gz",
        "data_preparation_mlcube": "1",
        "reference_model": "2",
        "data_evaluator_mlcube": "3",
        "docs_url": "",
        "demo_dataset_tarball_hash": "",
        "state": "OPERATION",
    }

    spy_init.assert_called_with(ANY, task_name="register_benchmark")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        bmk_info, skip_data_preparation_step=False, skip_compatibility_tests=False
    )

    spy_containers.assert_called_once()
    spy_models.assert_called_once()
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    assert spy_type.call_count == len(TEST_CONTAINERS)


def test_benchmark_registration_succeed(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_containers = mocker.patch(PATCH_GET_CONTAINERS, return_value=TEST_CONTAINERS)
    spy_type = mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=fake_container_type)
    spy_models = mocker.patch(PATCH_GET_MODELS, return_value=TEST_MODELS)
    spy_register = mocker.patch(PATCH_REGISTER, return_value=1)
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(
        "medperf.entities.benchmark.Benchmark.get", return_value=TEST_BENCHMARK
    )
    mocker.patch("medperf.entities.cube.Cube.get", return_value=TEST_CONTAINERS[0])
    mocker.patch("medperf.entities.model.Model.get", return_value=TEST_CONTAINERS[1])

    page.open(BASE_URL.format("/benchmarks/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.click(page.ALREADY_PREPARED)
    page.register_benchmark(
        name="test_benchmark",
        description="test description",
        reference_dataset="https://test.com/test.tar.gz",
        data_preparator="data-prep",
        reference_model="ref-model",
        metrics="metrics",
    )

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(popup_modal)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering benchmark completed successfully"
    )

    page.wait_for_url_change(old_url)
    assert "/benchmarks/ui/display/1" in page.current_url

    bmk_info = {
        "name": "test_benchmark",
        "description": "test description",
        "demo_dataset_tarball_url": "https://test.com/test.tar.gz",
        "data_preparation_mlcube": "1",
        "reference_model": "2",
        "data_evaluator_mlcube": "3",
        "docs_url": "",
        "demo_dataset_tarball_hash": "",
        "state": "OPERATION",
    }

    spy_init.assert_called_with(ANY, task_name="register_benchmark")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        bmk_info, skip_data_preparation_step=True, skip_compatibility_tests=False
    )

    spy_containers.assert_called_once()
    spy_models.assert_called_once()
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()

    assert spy_type.call_count == len(TEST_CONTAINERS)


def test_benchmark_registration_page_task_running(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_GET_CONTAINERS, return_value=[])
    mocker.patch(PATCH_GET_MODELS, return_value=[])

    web_app.state.task_running = True
    web_app.state.task.running = True

    page.open(BASE_URL.format("/benchmarks/register/ui"))

    name = page.find(page.NAME)
    description = page.find(page.DESCRIPTION)
    ref_dataset = page.find(page.REF_DATASET)
    already_prepared = page.find(page.ALREADY_PREPARED)
    not_prepared = page.find(page.NOT_PREPARED)
    data_prep = page.find(page.DATA_PREP)
    ref_model = page.find(page.REF_MODEL)
    metrics = page.find(page.METRICS)

    assert not name.is_enabled()
    assert not description.is_enabled()
    assert not ref_dataset.is_enabled()
    assert not already_prepared.is_enabled()
    assert not not_prepared.is_enabled()
    assert not data_prep.is_enabled()
    assert not ref_model.is_enabled()
    assert not metrics.is_enabled()
    assert not page.find(page.REGISTER).is_enabled()

    assert name.get_attribute("value") == ""
    assert description.get_attribute("value") == ""
    assert ref_dataset.get_attribute("value") == ""
    assert not already_prepared.is_selected()
    assert not not_prepared.is_selected()
    assert data_prep.get_attribute("value") == ""
    assert ref_model.get_attribute("value") == ""
    assert metrics.get_attribute("value") == ""

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.RESUME_SCRIPT)

    spy_init.assert_not_called()
    spy_event_gen.assert_not_called()
    spy_task_id.assert_not_called()
    spy_reset.assert_not_called()
    spy_notifs.assert_not_called()
    ui.end_task.assert_not_called()


def test_benchmark_registration_page_task_running_form_data(
    page, mocker, ui, patch_common
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_GET_CONTAINERS, return_value=TEST_CONTAINERS)
    mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=fake_container_type)
    mocker.patch(PATCH_GET_MODELS, return_value=TEST_MODELS)

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "register_benchmark"
    web_app.state.task.formData = {
        "name": "test_benchmark",
        "description": "test description",
        "reference_dataset_tarball_url": "https://test.com/test.tar.gz",
        "skip_data_preparation_step": "true",
        "data_preparation_container": "1",
        "reference_model": "2",
        "evaluator_container": "3",
        "skip_compatibility_tests": "false",
    }

    page.open(BASE_URL.format("/benchmarks/register/ui"))

    skip_tests = page.find(page.SKIP_TESTS)
    require_tests = page.find(page.REQUIRE_TESTS)
    name = page.find(page.NAME)
    description = page.find(page.DESCRIPTION)
    ref_dataset = page.find(page.REF_DATASET)
    already_prepared = page.find(page.ALREADY_PREPARED)
    not_prepared = page.find(page.NOT_PREPARED)
    data_prep = page.find(page.DATA_PREP)
    ref_model = page.find(page.REF_MODEL)
    metrics = page.find(page.METRICS)

    assert not skip_tests.is_enabled()
    assert not require_tests.is_enabled()
    assert not name.is_enabled()
    assert not description.is_enabled()
    assert not ref_dataset.is_enabled()
    assert not already_prepared.is_enabled()
    assert not not_prepared.is_enabled()
    assert not data_prep.is_enabled()
    assert not ref_model.is_enabled()
    assert not metrics.is_enabled()

    assert require_tests.is_selected()
    assert require_tests.get_attribute("value") == "false"
    assert name.get_attribute("value") == "test_benchmark"
    assert description.get_attribute("value") == "test description"
    assert ref_dataset.get_attribute("value") == "https://test.com/test.tar.gz"
    assert already_prepared.get_attribute("value") == "true"
    assert already_prepared.is_selected()
    assert data_prep.get_attribute("value") == "1"
    assert ref_model.get_attribute("value") == "2"
    assert metrics.get_attribute("value") == "3"

    register_btn = page.find(page.REGISTER)

    assert not register_btn.is_enabled()
    assert page.element_contains_spinner(register_btn)

    page.driver.find_element(*page.RESUME_SCRIPT)

    spy_event_gen.assert_called_once_with(ANY, True)

    spy_init.assert_not_called()
    spy_task_id.assert_not_called()
    spy_reset.assert_not_called()
    spy_notifs.assert_not_called()
    ui.end_task.assert_not_called()
