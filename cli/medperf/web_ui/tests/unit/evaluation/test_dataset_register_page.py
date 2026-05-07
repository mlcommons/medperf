from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.dataset.register_page import RegDatasetPage

import pytest
from unittest.mock import ANY
from medperf.tests.mocks.benchmark import TestBenchmark
import medperf.web_ui.events as events_module
from medperf.web_ui.app import web_app
from selenium.common.exceptions import NoSuchElementException

from medperf.web_ui.tests.unit.helpers import stub_event_generator

import time


BASE_URL = tests_config.BASE_URL
PATCH_GET_BENCHMARKS = "medperf.entities.benchmark.Benchmark.all"
PATCH_FOLDER_BROWSE = "medperf.web_ui.api.routes.{}"
PATCH_REGISTER = "medperf.commands.dataset.submit.DataCreation.run"
PATCH_ROUTE = "medperf.web_ui.datasets.routes.{}"

TEST_BENCHMARKS = [
    TestBenchmark(id=1, name="test_benchmark1"),
    TestBenchmark(id=2, name="test_benchmark2"),
]

TEST_FOLDERS = ["test_folder1", "test_folder2"]


def _picker_shown_path(page) -> str:
    raw = page.get_text(page.PICKER_PATH)
    for prefix in ("Select Path:", "Selected File:"):
        if prefix in raw:
            return raw.split(prefix, 1)[1].strip()
    return raw.strip()


def _wait_picker_shown_path(page, expected: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _picker_shown_path(page) == expected:
            return
        time.sleep(0.05)
    assert _picker_shown_path(page) == expected


def fake_isdir(p):
    return p == "/" or "test_folder" in p


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification

    return (init, reset, notifs)


@pytest.fixture()
def patch_folder_browsing(mocker, comms):
    mocker.patch(PATCH_FOLDER_BROWSE.format("Path.home"), return_value="")
    mocker.patch(PATCH_FOLDER_BROWSE.format("os.path.exists"), return_value=True)
    mocker.patch(
        PATCH_FOLDER_BROWSE.format("os.path.isdir"),
        side_effect=fake_isdir,
    )
    mocker.patch(PATCH_FOLDER_BROWSE.format("os.listdir"), return_value=TEST_FOLDERS)


@pytest.fixture
def page(driver):
    return RegDatasetPage(driver)


def test_dataset_registration_page_content(page, mocker):
    spy_benchmarks = mocker.patch(PATCH_GET_BENCHMARKS, return_value=[])

    page.open(BASE_URL.format("/datasets/register/ui"))

    page.wait_for_presence_selector(page.FORM)

    page.wait_for_presence_selector(page.BENCHMARK)

    page.wait_for_presence_selector(page.NAME)
    page.wait_for_presence_selector(page.NAME_TOOLTIP)

    page.wait_for_presence_selector(page.DESCRIPTION)
    page.wait_for_presence_selector(page.DESCRIPTION_TOOLTIP)

    page.wait_for_presence_selector(page.LOCATION)
    page.wait_for_presence_selector(page.LOCATION_TOOLTIP)

    page.wait_for_presence_selector(page.DATA)
    page.wait_for_presence_selector(page.DATA_BROWSE)
    page.wait_for_presence_selector(page.DATA_TOOLTIP)

    page.wait_for_presence_selector(page.LABELS)
    page.wait_for_presence_selector(page.LABELS_BROWSE)
    page.wait_for_presence_selector(page.LABELS_TOOLTIP)

    page.wait_for_presence_selector(page.PICKER_MODAL)
    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.TEXT_CONTAINER)
    page.wait_for_presence_selector(page.PROMPT_CONTAINER)

    assert page.get_text(page.HEADER) == "Register a New Dataset"
    assert page.get_text(page.BENCHMARK_LABEL) == "Select Benchmark"
    assert page.get_text(page.NAME_LABEL) == "Dataset Name"
    assert page.get_text(page.DESCRIPTION_LABEL) == "Description"
    assert page.get_text(page.LOCATION_LABEL) == "Location"
    assert page.get_text(page.DATA_LABEL) == "Data Folder"
    assert page.get_text(page.LABELS_LABEL) == "Labels Folder"
    assert page.get_text(page.REGISTER) == "Register Dataset"

    spy_benchmarks.assert_called_once()


def test_dataset_registration_page_tooltips(page, mocker):
    mocker.patch(PATCH_GET_BENCHMARKS, return_value=[])

    page.open(BASE_URL.format("/datasets/register/ui"))

    name_tooltip = page.find(page.NAME_TOOLTIP)
    description_tooltip = page.find(page.DESCRIPTION_TOOLTIP)
    location_tooltip = page.find(page.LOCATION_TOOLTIP)
    data_tooltip = page.find(page.DATA_TOOLTIP)
    labels_tooltip = page.find(page.LABELS_TOOLTIP)

    assert (
        name_tooltip.get_attribute("title") == "Name of the dataset you are registering"
    )
    assert description_tooltip.get_attribute("title") == (
        "Description of the dataset you are registering"
    )
    assert (
        location_tooltip.get_attribute("title")
        == "Location of the dataset you are registering"
    )
    assert data_tooltip.get_attribute("title") == "Path to the data folder"
    assert labels_tooltip.get_attribute("title") == "Path to the labels folder"


def test_dataset_registration_folder_picker_cancel(page, patch_folder_browsing):
    page.open(BASE_URL.format("/datasets/register/ui"))

    folder_picker = page.find(page.PICKER_MODAL)
    page.click(page.DATA_BROWSE)
    page.wait_for_visibility_element(folder_picker)
    page.click(page.PICKER_CANCEL)
    page.wait_for_invisibility_element(folder_picker)

    page.click(page.LABELS_BROWSE)
    page.wait_for_visibility_element(folder_picker)
    page.click(page.PICKER_CANCEL)
    page.wait_for_invisibility_element(folder_picker)


def test_dataset_registration_folder_picker_path(page, patch_folder_browsing):
    folder1 = TEST_FOLDERS[0]
    folder2 = TEST_FOLDERS[1]
    folder1_path = "/" + folder1
    folder2_path = "/" + folder2

    page.open(BASE_URL.format("/datasets/register/ui"))

    folder_picker = page.find(page.PICKER_MODAL)
    page.click(page.DATA_BROWSE)
    page.wait_for_visibility_element(folder_picker)
    folders_list = page.find_elements(page.PICKER_FOLDERS)
    classes = [e.get_attribute("class") for e in folders_list]

    assert len(folders_list) == len(TEST_FOLDERS) + 1  # + {.. (parent)} entry
    assert all("file-item" not in c for c in classes)
    assert folders_list[0].text == ".. (parent)"
    assert "parent-disabled" in folders_list[0].get_attribute("class")
    assert folders_list[1].text == folder1
    assert folders_list[1].get_attribute("data-path") == folder1_path
    assert _picker_shown_path(page) == "/"

    folders_list[1].click()
    _wait_picker_shown_path(page, folder1_path)
    folders_list = page.find_elements(page.PICKER_FOLDERS)

    assert folders_list[2].text == folder2
    assert folders_list[2].get_attribute("data-path") == folder1_path + folder2_path
    assert _picker_shown_path(page) == folder1_path

    page.click(page.PICKER_SELECT)
    page.wait_for_invisibility_element(folder_picker)

    assert page.get_attribute(page.DATA, "value") == folder1_path

    page.click(page.LABELS_BROWSE)
    page.wait_for_visibility_element(folder_picker)
    folders_list = page.find_elements(page.PICKER_FOLDERS)

    assert len(folders_list) == len(TEST_FOLDERS) + 1  # {.. (parent)} entry
    assert folders_list[0].text == ".. (parent)"
    assert "parent-disabled" not in folders_list[0].get_attribute("class")
    assert _picker_shown_path(page) == folder1_path

    folders_list[0].click()
    _wait_picker_shown_path(page, "/")

    folders_list = page.find_elements(page.PICKER_FOLDERS)

    assert folders_list[2].get_attribute("data-path") == folder2_path
    assert folders_list[2].text == folder2

    folders_list[2].click()
    _wait_picker_shown_path(page, folder2_path)

    page.click(page.PICKER_SELECT)
    page.wait_for_invisibility_element(folder_picker)

    assert page.get_attribute(page.LABELS, "value") == folder2_path


def test_dataset_registration_fails(page, mocker, ui, patch_common):
    error_message = "Dataset registration test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_register = mocker.patch(PATCH_REGISTER, side_effect=Exception(error_message))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_GET_BENCHMARKS, return_value=TEST_BENCHMARKS)

    page.open(BASE_URL.format("/datasets/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.register_dataset(
        benchmark=TEST_BENCHMARKS[0].name,
        name="test_dataset",
        description="test description",
        location="test_location",
        data_path="test_path",
        labels_path="test_path",
    )

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while registering dataset"
    )
    assert error_message in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_with(ANY, task_name="register_dataset")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        benchmark_uid=TEST_BENCHMARKS[0].id,
        name="test_dataset",
        description="test description",
        location="test_location",
        data_path="test_path",
        labels_path="test_path",
        approved=ANY,
        metadata_path=ANY,
        prep_cube_uid=ANY,
        submit_as_prepared=ANY,
    )

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_dataset_registration_succeed(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_register = mocker.patch(PATCH_REGISTER, return_value=1)
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_GET_BENCHMARKS, return_value=TEST_BENCHMARKS)

    page.open(BASE_URL.format("/datasets/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.register_dataset(
        benchmark=TEST_BENCHMARKS[0].name,
        name="test_dataset",
        description="test description",
        location="test_location",
        data_path="test_path",
        labels_path="test_path",
    )

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(popup_modal)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering dataset completed successfully"
    )

    page.wait_for_url_change(old_url)
    assert "/datasets/ui/display/1" in page.current_url

    spy_init.assert_called_with(ANY, task_name="register_dataset")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        benchmark_uid=TEST_BENCHMARKS[0].id,
        name="test_dataset",
        description="test description",
        location="test_location",
        data_path="test_path",
        labels_path="test_path",
        approved=ANY,
        metadata_path=ANY,
        prep_cube_uid=ANY,
        submit_as_prepared=ANY,
    )

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_dataset_registration_page_task_running(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_GET_BENCHMARKS, return_value=[])

    web_app.state.task_running = True
    web_app.state.task.running = True

    page.open(BASE_URL.format("/datasets/register/ui"))

    benchmark = page.find(page.BENCHMARK)
    name = page.find(page.NAME)
    description = page.find(page.DESCRIPTION)
    location = page.find(page.LOCATION)
    data = page.find(page.DATA)
    labels = page.find(page.LABELS)

    assert not benchmark.is_enabled()
    assert not name.is_enabled()
    assert not description.is_enabled()
    assert not location.is_enabled()
    assert not data.is_enabled()
    assert not labels.is_enabled()
    assert not page.find(page.REGISTER).is_enabled()

    assert benchmark.get_attribute("value") == ""
    assert name.get_attribute("value") == ""
    assert description.get_attribute("value") == ""
    assert location.get_attribute("value") == ""
    assert data.get_attribute("value") == ""
    assert labels.get_attribute("value") == ""

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.RESUME_SCRIPT)

    spy_init.assert_not_called()
    spy_event_gen.assert_not_called()
    spy_task_id.assert_not_called()
    spy_reset.assert_not_called()
    spy_notifs.assert_not_called()
    ui.end_task.assert_not_called()


def test_dataset_registration_page_task_running_form_data(
    page, mocker, ui, patch_common
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(PATCH_GET_BENCHMARKS, return_value=TEST_BENCHMARKS)

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "register_dataset"
    web_app.state.task.formData = {
        "benchmark": "1",
        "name": "test dataset",
        "description": "test description",
        "location": "test location",
        "data_path": "test_path",
        "labels_path": "test_path",
    }

    page.open(BASE_URL.format("/datasets/register/ui"))

    benchmark = page.find(page.BENCHMARK)
    name = page.find(page.NAME)
    description = page.find(page.DESCRIPTION)
    location = page.find(page.LOCATION)
    data = page.find(page.DATA)
    labels = page.find(page.LABELS)

    assert not benchmark.is_enabled()
    assert not name.is_enabled()
    assert not description.is_enabled()
    assert not location.is_enabled()
    assert not data.is_enabled()
    assert not labels.is_enabled()

    assert benchmark.get_attribute("value") == "1"
    assert name.get_attribute("value") == "test dataset"
    assert description.get_attribute("value") == "test description"
    assert location.get_attribute("value") == "test location"
    assert data.get_attribute("value") == "test_path"
    assert labels.get_attribute("value") == "test_path"

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
