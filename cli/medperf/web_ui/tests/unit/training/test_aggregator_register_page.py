import datetime
from types import SimpleNamespace
from unittest.mock import ANY

import pytest
import medperf.web_ui.events as events_module
from medperf.web_ui.app import web_app
from selenium.common.exceptions import NoSuchElementException

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.aggregator.register_page import RegAggregatorPage
from medperf.web_ui.tests.unit.helpers import stub_event_generator, switch_to_ui_mode

BASE_URL = tests_config.BASE_URL
PATCH_GET_CONTAINERS = "medperf.entities.cube.Cube.all"
PATCH_REGISTER = "medperf.commands.aggregator.submit.SubmitAggregator.run"
PATCH_ROUTE = "medperf.web_ui.aggregators.routes.{}"

TEST_AGG = SimpleNamespace(
    id=9,
    name="agg-9",
    owner=1,
    address="127.0.0.1",
    port=7000,
    admin_port=7001,
    created_at=datetime.datetime(2026, 1, 1),
    modified_at=datetime.datetime(2026, 1, 2),
    get_training_experiments=lambda: [SimpleNamespace(id=77, name="tr-77")],
)

TEST_AGG_CONTAINER = SimpleNamespace(id=1, name="agg-container")


@pytest.fixture(autouse=True)
def patch_login(mocker):
    mocker.patch(
        "medperf.web_ui.aggregators.routes.get_medperf_user_data",
        return_value={"id": 1, "email": "training-ui-test@local"},
    )


@pytest.fixture
def page(driver):
    return RegAggregatorPage(driver)


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    return (init, reset, ui.add_notification)


def test_aggregator_register_page_content(page, mocker):
    mocker.patch(PATCH_GET_CONTAINERS, return_value=[])

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/register/ui"))

    page.wait_for_presence_selector(page.FORM)
    assert page.get_text(page.HEADER) == "Register New Aggregator"
    assert page.get_text(page.NAME_LABEL) == "Name"
    assert page.get_text(page.ADDRESS_LABEL) == "Address"
    assert page.get_text(page.PORT_LABEL) == "Port"
    assert page.get_text(page.ADMIN_PORT_LABEL) == "Admin Port"
    assert page.get_text(page.CONTAINER_LABEL) == "Aggregation Container"


def test_aggregator_registration_fails(page, mocker, ui, patch_common):
    error_message = "Aggregator registration failed test"
    containers = [TEST_AGG_CONTAINER]
    spy_init, spy_reset, spy_notifs = patch_common
    mocker.patch(PATCH_GET_CONTAINERS, return_value=containers)
    spy_register = mocker.patch(PATCH_REGISTER, side_effect=Exception(error_message))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)
    page.register_aggregator("agg-name", "127.0.0.1", 7000, 7001, "agg-container")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while registering aggregator"
    )
    assert error_message in page.get_text(page.ERROR_TEXT)

    page.ensure_element_ready(error_modal.find_element(*page.ERROR_HIDE))
    error_modal.find_element(*page.ERROR_HIDE).click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_with(ANY, task_name="register_aggregator")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        name="agg-name",
        address="127.0.0.1",
        port=7000,
        admin_port=7001,
        aggregation_mlcube=1,
    )
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()


def test_aggregator_registration_succeed(page, mocker, ui, patch_common):
    containers = [TEST_AGG_CONTAINER]
    spy_init, spy_reset, spy_notifs = patch_common
    mocker.patch(PATCH_GET_CONTAINERS, return_value=containers)
    spy_register = mocker.patch(PATCH_REGISTER, return_value=1)
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(
        "medperf.web_ui.aggregators.routes.Aggregator.get", return_value=TEST_AGG
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)
    page.register_aggregator("agg-name", "127.0.0.1", 7000, 7001, "agg-container")
    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering aggregator completed successfully"
    )
    page.wait_for_url_change(old_url)
    assert "/aggregators/ui/display/1" in page.current_url

    spy_init.assert_called_with(ANY, task_name="register_aggregator")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_with(
        name="agg-name",
        address="127.0.0.1",
        port=7000,
        admin_port=7001,
        aggregation_mlcube=1,
    )
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()


def test_aggregator_registration_page_task_running(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"
    mocker.patch(PATCH_GET_CONTAINERS, return_value=[])
    web_app.state.task_running = True
    web_app.state.task.running = True

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/register/ui"))
    assert not page.find(page.NAME).is_enabled()
    assert not page.find(page.ADDRESS).is_enabled()
    assert not page.find(page.PORT).is_enabled()
    assert not page.find(page.ADMIN_PORT).is_enabled()
    assert not page.find(page.AGGREGATION_MLCUBE).is_enabled()
    assert not page.find(page.REGISTER).is_enabled()

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.RESUME_SCRIPT)
    spy_init.assert_not_called()
    spy_event_gen.assert_not_called()
    spy_task_id.assert_not_called()
    spy_reset.assert_not_called()
    spy_notifs.assert_not_called()
    ui.end_task.assert_not_called()


def test_aggregator_registration_page_task_running_form_data(
    page, mocker, ui, patch_common
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"
    mocker.patch(PATCH_GET_CONTAINERS, return_value=[TEST_AGG_CONTAINER])
    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "register_aggregator"
    web_app.state.task.formData = {
        "name": "agg-name",
        "address": "127.0.0.1",
        "port": "7000",
        "admin_port": "7001",
        "aggregation_mlcube": "1",
    }

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/register/ui"))
    assert page.find(page.NAME).get_attribute("value") == "agg-name"
    assert page.find(page.ADDRESS).get_attribute("value") == "127.0.0.1"
    assert page.find(page.PORT).get_attribute("value") == "7000"
    assert page.find(page.ADMIN_PORT).get_attribute("value") == "7001"
    assert page.find(page.AGGREGATION_MLCUBE).get_attribute("value") == "1"
    page.driver.find_element(*page.RESUME_SCRIPT)
    spy_event_gen.assert_called_once_with(ANY, True)
    spy_init.assert_not_called()
    spy_task_id.assert_not_called()
    spy_reset.assert_not_called()
    spy_notifs.assert_not_called()
    ui.end_task.assert_not_called()
