from medperf.tests.mocks.cube import TestCube
from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.container.register_page import RegContainerPage

import pytest
from unittest.mock import ANY
import medperf.web_ui.events as events_module
from medperf.web_ui.app import web_app
from selenium.common.exceptions import NoSuchElementException

from medperf.web_ui.tests.unit.helpers import stub_event_generator


BASE_URL = tests_config.BASE_URL
PATCH_GET_CONTAINERS = "medperf.entities.cube.Cube.all"
PATCH_REGISTER = "medperf.commands.mlcube.submit.SubmitCube.run"
PATCH_ROUTE = "medperf.web_ui.containers.routes.{}"
PATCH_BENCHMARK_ALL = "medperf.web_ui.containers.routes.Benchmark.all"
PATCH_GET_CONTAINER = "medperf.entities.cube.Cube.get"

TEST_CONTAINER = TestCube()


@pytest.fixture(autouse=True)
def _mock_benchmarks_for_container_register(mocker):
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification

    return (init, reset, notifs)


@pytest.fixture
def page(driver):
    return RegContainerPage(driver)


@pytest.fixture(autouse=True)
def patch_login(mocker):
    mocker.patch(
        "medperf.web_ui.containers.routes.get_medperf_user_data",
        return_value={"id": 1, "email": "webui-test@local"},
    )
    mocker.patch(PATCH_GET_CONTAINER, return_value=TEST_CONTAINER)


def test_container_registration_page_content(page):
    page.open(BASE_URL.format("/containers/register/ui"))

    page.wait_for_presence_selector(page.FORM)

    page.wait_for_presence_selector(page.NAME)
    page.wait_for_presence_selector(page.NAME_TOOLTIP)

    page.wait_for_presence_selector(page.MANIFEST)
    page.wait_for_presence_selector(page.MANIFEST_TOOLTIP)

    page.wait_for_presence_selector(page.PARAMETERS)
    page.wait_for_presence_selector(page.PARAMETERS_TOOLTIP)

    page.wait_for_presence_selector(page.ADDITIONAL)
    page.wait_for_presence_selector(page.ADDITIONAL_TOOLTIP)

    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.PAGE_MODAL)
    page.wait_for_presence_selector(page.TEXT_CONTAINER)
    page.wait_for_presence_selector(page.PROMPT_CONTAINER)

    assert page.get_text(page.HEADER) == "Register a New Container"
    assert page.get_text(page.NAME_LABEL) == "Container name"
    assert page.get_text(page.MANIFEST_LABEL) == "Container Config File"
    assert page.get_text(page.PARAMETERS_LABEL) == "Parameters File"
    assert page.get_text(page.ADDITIONAL_LABEL) == "Additional Files URL"
    assert page.get_text(page.REGISTER) == "Register container"


def test_container_registration_page_tooltips(page):
    page.open(BASE_URL.format("/containers/register/ui"))

    name_tooltip = page.find(page.NAME_TOOLTIP)
    manifest_tooltip = page.find(page.MANIFEST_TOOLTIP)
    parameters_tooltip = page.find(page.PARAMETERS_TOOLTIP)
    additional_tooltip = page.find(page.ADDITIONAL_TOOLTIP)

    assert (
        name_tooltip.get_attribute("title")
        == "Name of the container you are registering"
    )
    assert manifest_tooltip.get_attribute("title") == (
        "Path to the container config file for the container you are registering"
    )
    assert parameters_tooltip.get_attribute("title") == (
        "Path to the parameters file for the container you are registering (Optional)"
    )
    assert additional_tooltip.get_attribute("title") == (
        "URL of the additional files tarball for the container you are registering (Optional)"
    )


def test_container_registration_fails(page, mocker, ui, patch_common):
    error_message = "Container registration test failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_register = mocker.patch(PATCH_REGISTER, side_effect=Exception(error_message))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format("/containers/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    test_container = {
        "name": "test_container",
        "manifest": "test_manifest.yaml",
        "parameters": "",
        "additional": "",
    }

    page.register_container(test_container)

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while registering container"
    )
    assert error_message in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_with(ANY, task_name="register_container")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        {
            "name": test_container["name"],
            "additional_files_tarball_url": test_container["additional"],
            "additional_files_tarball_hash": "",
            "state": "OPERATION",
        },
        container_config=test_container["manifest"],
        parameters_config=test_container["parameters"] or None,
        decryption_key=None,
    )

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_container_registration_fails_with_optional(page, mocker, ui, patch_common):
    error_message = "Container registration test with optional failed"

    spy_init, spy_reset, spy_notifs = patch_common
    spy_register = mocker.patch(PATCH_REGISTER, side_effect=Exception(error_message))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format("/containers/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    test_container = {
        "name": "test_container",
        "manifest": "test_manifest.yaml",
        "parameters": "test_parameters.yaml",
        "additional": "test_additional.yaml",
    }

    page.register_container(test_container)

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while registering container"
    )
    assert error_message in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()

    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_with(ANY, task_name="register_container")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        {
            "name": test_container["name"],
            "additional_files_tarball_url": test_container["additional"],
            "additional_files_tarball_hash": "",
            "state": "OPERATION",
        },
        container_config=test_container["manifest"],
        parameters_config=test_container["parameters"],
        decryption_key=None,
    )

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_container_registration_succeed(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_register = mocker.patch(PATCH_REGISTER, return_value=1)
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format("/containers/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    test_container = {
        "name": "test_container",
        "manifest": "test_manifest.yaml",
        "parameters": "",
        "additional": "",
    }

    page.register_container(test_container)

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(popup_modal)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering container completed successfully"
    )

    page.wait_for_url_change(old_url)
    assert "/containers/ui/display/1" in page.current_url

    spy_init.assert_called_with(ANY, task_name="register_container")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        {
            "name": test_container["name"],
            "additional_files_tarball_url": test_container["additional"],
            "additional_files_tarball_hash": "",
            "state": "OPERATION",
        },
        container_config=test_container["manifest"],
        parameters_config=test_container["parameters"] or None,
        decryption_key=None,
    )

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_container_registration_succeed_with_optional(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_register = mocker.patch(PATCH_REGISTER, return_value=1)
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    page.open(BASE_URL.format("/containers/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    test_container = {
        "name": "test_container",
        "manifest": "test_manifest.yaml",
        "parameters": "test_parameters.yaml",
        "additional": "test_additional.yaml",
    }

    page.register_container(test_container)

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    page.wait_for_visibility_element(popup_modal)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering container completed successfully"
    )

    page.wait_for_url_change(old_url)
    assert "/containers/ui/display/1" in page.current_url

    spy_init.assert_called_with(ANY, task_name="register_container")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        {
            "name": test_container["name"],
            "additional_files_tarball_url": test_container["additional"],
            "additional_files_tarball_hash": "",
            "state": "OPERATION",
        },
        container_config=test_container["manifest"],
        parameters_config=test_container["parameters"],
        decryption_key=None,
    )

    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()

    ui.end_task.assert_called_once()


def test_contianer_registration_page_task_running(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    web_app.state.task_running = True
    web_app.state.task.running = True

    page.open(BASE_URL.format("/containers/register/ui"))

    name = page.find(page.NAME)
    manifest = page.find(page.MANIFEST)
    parameters = page.find(page.PARAMETERS)
    additional = page.find(page.ADDITIONAL)

    assert not name.is_enabled()
    assert not manifest.is_enabled()
    assert not parameters.is_enabled()
    assert not additional.is_enabled()
    assert not page.find(page.REGISTER).is_enabled()

    assert name.get_attribute("value") == ""
    assert manifest.get_attribute("value") == ""
    assert parameters.get_attribute("value") == ""
    assert additional.get_attribute("value") == ""

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.RESUME_SCRIPT)

    spy_init.assert_not_called()
    spy_event_gen.assert_not_called()
    spy_task_id.assert_not_called()
    spy_reset.assert_not_called()
    spy_notifs.assert_not_called()
    ui.end_task.assert_not_called()


def test_container_registration_page_task_running_form_data(
    page, mocker, ui, patch_common
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "register_container"
    web_app.state.task.formData = {
        "name": "test_container",
        "container_file": "test_manifest.yaml",
        "parameters_file": "test_parameters.yaml",
        "additional_file": "test_additional.yaml",
    }

    page.open(BASE_URL.format("/containers/register/ui"))

    name = page.find(page.NAME)
    manifest = page.find(page.MANIFEST)
    parameters = page.find(page.PARAMETERS)
    additional = page.find(page.ADDITIONAL)

    assert not name.is_enabled()
    assert not manifest.is_enabled()
    assert not parameters.is_enabled()
    assert not additional.is_enabled()

    assert name.get_attribute("value") == "test_container"
    assert manifest.get_attribute("value") == "test_manifest.yaml"
    assert parameters.get_attribute("value") == "test_parameters.yaml"
    assert additional.get_attribute("value") == "test_additional.yaml"

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
