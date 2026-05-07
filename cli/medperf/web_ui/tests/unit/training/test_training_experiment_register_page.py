from types import SimpleNamespace
from unittest.mock import ANY

from medperf.tests.mocks.cube import TestCube
import pytest
import medperf.web_ui.events as events_module
from medperf.web_ui.app import web_app
from selenium.common.exceptions import NoSuchElementException

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.training.register_page import RegTrainingPage
from medperf.web_ui.tests.unit.helpers import stub_event_generator, switch_to_ui_mode

BASE_URL = tests_config.BASE_URL
PATCH_GET_CONTAINERS = "medperf.entities.cube.Cube.all"
PATCH_GET_CONTAINERS_TYPE = "medperf.web_ui.training.routes.get_container_type"
PATCH_REGISTER = "medperf.commands.training.submit.SubmitTrainingExp.run"
PATCH_ROUTE = "medperf.web_ui.training.routes.{}"

TEST_CONTAINERS = [TestCube(id=1, name="prep"), TestCube(id=2, name="fl")]


@pytest.fixture(autouse=True)
def patch_login(mocker):
    mocker.patch(
        "medperf.web_ui.training.routes.get_medperf_user_data",
        return_value={"id": 1, "email": "training-ui-test@local"},
    )


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    return (init, reset, ui.add_notification)


@pytest.fixture
def page(driver):
    return RegTrainingPage(driver)


def _cube_type(c):
    return "data-prep-container" if c.id == 1 else "fl-container"


def test_training_register_page_content(page, mocker):
    mocker.patch(PATCH_GET_CONTAINERS, return_value=TEST_CONTAINERS)
    mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=_cube_type)

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/register/ui"))

    page.wait_for_presence_selector(page.FORM)
    assert page.get_text(page.HEADER) == "Register New Training Experiment"
    assert page.get_text(page.NAME_LABEL) == "Name"
    assert page.get_text(page.DESCRIPTION_LABEL) == "Description"
    assert page.get_text(page.DATA_PREP_LABEL) == "Data Preparation Container"
    assert page.get_text(page.FL_LABEL) == "FL Container"


def test_training_register_page_tooltips(page, mocker):
    mocker.patch(PATCH_GET_CONTAINERS, return_value=TEST_CONTAINERS)
    mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=_cube_type)

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/register/ui"))

    name_tooltip = page.find(page.NAME_TOOLTIP)
    description_tooltip = page.find(page.DESCRIPTION_TOOLTIP)
    data_prep_tooltip = page.find(page.DATA_PREP_TOOLTIP)

    assert (
        name_tooltip.get_attribute("title")
        == "Name of the training experiment you are registering"
    )
    assert description_tooltip.get_attribute("title") == (
        "Short description of the training experiment"
    )
    assert data_prep_tooltip.get_attribute("title") == (
        "Data preparation container used to preprocess datasets for this experiment."
        + " Must match the one used by datasets you associate."
    )


def test_training_registration_fails(page, mocker, ui, patch_common):
    error_message = "Training registration failed test"
    spy_init, spy_reset, spy_notifs = patch_common
    mocker.patch(PATCH_GET_CONTAINERS, return_value=TEST_CONTAINERS)
    mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=_cube_type)
    spy_register = mocker.patch(PATCH_REGISTER, side_effect=Exception(error_message))
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/register/ui"))
    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)
    page.register_training("tr-name", "desc", "prep", "fl", "None")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something when wrong while registering training experiment"
    )
    assert error_message in page.get_text(page.ERROR_TEXT)

    spy_init.assert_called_with(ANY, task_name="register_training_experiment")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_once()
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()


def test_training_registration_succeed(page, mocker, ui, patch_common):
    spy_init, spy_reset, spy_notifs = patch_common
    mocker.patch(PATCH_GET_CONTAINERS, return_value=TEST_CONTAINERS)
    mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=_cube_type)
    spy_register = mocker.patch(PATCH_REGISTER, return_value=1)
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")

    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"

    mocker.patch(
        "medperf.entities.training_exp.TrainingExp.get",
        return_value=SimpleNamespace(
            id=1,
            name="tr-name",
            owner=1,
            state="DEVELOPMENT",
            approval_status="APPROVED",
            description="desc",
            docs_url="",
            data_preparation_mlcube=1,
            fl_mlcube=2,
            fl_admin_mlcube=None,
            plan={},
            created_at=None,
            modified_at=None,
        ),
    )
    mocker.patch("medperf.entities.cube.Cube.get", return_value=TEST_CONTAINERS[0])
    mocker.patch(
        "medperf.commands.association.utils.get_experiment_associations",
        return_value=[],
    )
    mocker.patch("medperf.config.comms.get_experiment_aggregator", return_value=None)
    mocker.patch(
        "medperf.config.comms.get_experiment_event", return_value={"finished": True}
    )
    mocker.patch("medperf.entities.aggregator.Aggregator.all", return_value=[])

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/register/ui"))
    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)
    page.register_training("tr-name", "desc", "prep", "fl", "None")

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering training experiment completed successfully"
    )
    page.wait_for_url_change(old_url)
    assert "/training/ui/display/1" in page.current_url

    spy_init.assert_called_with(ANY, task_name="register_training_experiment")
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_register.assert_called_once()
    spy_task_id.assert_called_once()
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()


def test_training_registration_page_task_running(page, mocker, ui, patch_common):
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
    page.open(BASE_URL.format("/training/register/ui"))

    name = page.find(page.NAME)
    description = page.find(page.DESCRIPTION)
    data_prep = page.find(page.DATA_PREP)
    fl = page.find(page.FL)
    fl_admin = page.find(page.FL_ADMIN)
    register = page.find(page.REGISTER)

    assert not name.is_enabled()
    assert not description.is_enabled()
    assert not data_prep.is_enabled()
    assert not fl.is_enabled()
    assert not fl_admin.is_enabled()
    assert not register.is_enabled()

    assert name.get_attribute("value") == ""
    assert description.get_attribute("value") == ""
    assert data_prep.get_attribute("value") == ""
    assert fl.get_attribute("value") == ""
    assert fl_admin.get_attribute("value") == ""

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.RESUME_SCRIPT)

    spy_init.assert_not_called()
    spy_event_gen.assert_not_called()
    spy_task_id.assert_not_called()
    spy_reset.assert_not_called()
    spy_notifs.assert_not_called()
    ui.end_task.assert_not_called()


def test_training_registration_page_task_running_form_data(
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
    mocker.patch(PATCH_GET_CONTAINERS_TYPE, side_effect=_cube_type)
    web_app.state.task_running = True
    web_app.state.task.running = True
    web_app.state.task.name = "register_training_experiment"
    web_app.state.task.formData = {
        "name": "tr-name",
        "description": "desc",
        "data_preparation_container": "1",
        "fl_container": "2",
        "fl_admin_container": "",
    }

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/register/ui"))
    assert page.find(page.NAME).get_attribute("value") == "tr-name"
    assert page.find(page.DESCRIPTION).get_attribute("value") == "desc"
    assert page.find(page.DATA_PREP).get_attribute("value") == "1"
    assert page.find(page.FL).get_attribute("value") == "2"
    page.driver.find_element(*page.RESUME_SCRIPT)

    spy_event_gen.assert_called_once_with(ANY, True)
    spy_init.assert_not_called()
    spy_task_id.assert_not_called()
    spy_reset.assert_not_called()
    spy_notifs.assert_not_called()
    ui.end_task.assert_not_called()
