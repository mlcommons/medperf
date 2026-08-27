import datetime
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock

from medperf.tests.mocks.cube import TestCube
import pytest
from selenium.common.exceptions import NoSuchElementException

from medperf.enums import Status
from medperf.tests.mocks.training_exp import TestTrainingExp
from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.training.details_page import TrainingDetailsPage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode, stub_event_generator
import medperf.web_ui.events as events_module

BASE_URL = tests_config.BASE_URL
PATCH_ROUTE = "medperf.web_ui.training.routes.{}"

PREP_CUBE = TestCube(id=1, name="prep")
FL_CUBE = TestCube(id=2, name="fl")
TEST_CONTAINERS = [PREP_CUBE, FL_CUBE]
TEST_AGG = SimpleNamespace(id=5, name="agg", address="127.0.0.1", port=7000, owner=1)


def _base_exp(**overrides):
    defaults = dict(
        id=77,
        owner=1,
        name="train-77",
        data_preparation_mlcube=1,
        fl_mlcube=2,
        fl_admin_mlcube=None,
    )
    defaults.update(overrides)
    exp = TestTrainingExp(**defaults)
    exp.plan = overrides.pop("plan", {"epochs": 1})
    return exp


def _mock_common(
    mocker,
    exp,
    aggregator=None,
    event_finished=True,
    associations=None,
):
    mocker.patch("medperf.entities.training_exp.TrainingExp.get", return_value=exp)
    mocker.patch("medperf.entities.cube.Cube.get", return_value=PREP_CUBE)
    mocker.patch(
        "medperf.entities.training_exp.get_user_associations",
        return_value=associations or [],
    )
    mocker.patch(
        "medperf.entities.dataset.Dataset.get",
        return_value=MagicMock(id=31, name="d31"),
    )
    mocker.patch(
        "medperf.config.comms.get_experiment_aggregator",
        return_value=(
            {
                "id": aggregator.id,
                "name": aggregator.name,
                "owner": aggregator.owner,
                "config": {
                    "address": aggregator.address,
                    "port": aggregator.port,
                    "admin_port": 8001,
                },
                "aggregation_mlcube": 1,
            }
            if aggregator
            else None
        ),
    )
    mocker.patch(
        "medperf.config.comms.get_experiment_event",
        return_value={"finished": event_finished},
    )
    mocker.patch("medperf.entities.aggregator.Aggregator.all", return_value=[TEST_AGG])


@pytest.fixture(autouse=True)
def patch_login(mocker):
    data = {"id": 1, "email": "training-ui-test@local"}
    mocker.patch(
        "medperf.web_ui.common.read_user_account", return_value={"email": data["email"]}
    )
    mocker.patch("medperf.web_ui.common.get_medperf_user_data", return_value=data)
    mocker.patch(
        "medperf.web_ui.training.routes.get_medperf_user_data", return_value=data
    )


@pytest.fixture
def page(driver):
    return TrainingDetailsPage(driver)


@pytest.fixture()
def patch_common(mocker, ui):
    init = mocker.patch(PATCH_ROUTE.format("initialize_state_task"))
    reset = mocker.patch(PATCH_ROUTE.format("reset_state_task"))
    ui.add_notification = mocker.Mock()
    notifs = ui.add_notification
    return (init, reset, notifs)


@pytest.fixture()
def patch_task_events(mocker, ui):
    spy_event_gen = mocker.patch.object(
        events_module, "event_generator", side_effect=stub_event_generator
    )
    spy_task_id = mocker.spy(events_module, "_get_task_id")
    ui.end_task = mocker.Mock()
    ui.task_id = "test-id"
    return (spy_event_gen, spy_task_id)


def test_training_details_page_common_content(page, mocker):
    exp = TestTrainingExp(
        id=77,
        owner=1,
        name="train-77",
        state="DEVELOPMENT",
        approval_status="APPROVED",
        description="desc",
        docs_url="",
        fl_admin_mlcube=None,
        created_at=datetime.datetime(2026, 1, 1),
        modified_at=datetime.datetime(2026, 1, 2),
    )
    exp.plan = {"epochs": 1}
    mocker.patch("medperf.entities.training_exp.TrainingExp.get", return_value=exp)
    mocker.patch(
        "medperf.entities.cube.Cube.get",
        side_effect=lambda cube_uid: TEST_CONTAINERS[cube_uid - 1],
    )
    mocker.patch(
        "medperf.commands.association.utils.get_experiment_associations",
        return_value=[{"dataset": 31, "approval_status": "PENDING"}],
    )
    mocker.patch(
        "medperf.entities.dataset.Dataset.get",
        return_value=MagicMock(id=31, name="d31"),
    )
    mocker.patch("medperf.config.comms.get_experiment_aggregator", return_value=None)
    mocker.patch(
        "medperf.config.comms.get_experiment_event", return_value={"finished": True}
    )
    mocker.patch("medperf.entities.aggregator.Aggregator.all", return_value=[])

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    assert page.get_text(page.HEADER) == "train-77"
    assert page.get_text(page.DETAILS_HEADING) == "Details"
    assert page.get_text(page.ID_LABEL) == "Experiment ID"
    assert page.get_text(page.ID) == "77"
    assert page.get_text(page.OWNER_LABEL) == "Owner"
    assert page.get_text(page.DESCRIPTION_LABEL) == "Description"
    assert page.get_text(page.DESCRIPTION) == "desc"
    assert page.get_text(page.DOCUMENTATION_LABEL) == "Documentation"
    assert page.get_text(page.DOCUMENTATION_NA) == "Not Available"
    assert page.get_text(page.AGGREGATOR_HEADING) == "Aggregator"
    assert page.get_text(page.ACTIONS_HEADING) == "Actions"
    assert page.get_text(page.ASSOCIATIONS_HEADING) == "Dataset Associations"


def test_training_details_page_actions_content(page, mocker):
    exp = TestTrainingExp(
        id=77,
        owner=1,
        name="train-77",
        data_preparation_mlcube=1,
        fl_mlcube=2,
        fl_admin_mlcube=None,
    )
    exp.plan = {"epochs": 1}
    mocker.patch("medperf.entities.training_exp.TrainingExp.get", return_value=exp)
    mocker.patch(
        "medperf.entities.cube.Cube.get",
        return_value=PREP_CUBE,
    )
    mocker.patch(
        "medperf.commands.association.utils.get_experiment_associations",
        return_value=[],
    )
    mocker.patch(
        "medperf.entities.dataset.Dataset.get",
        return_value=MagicMock(id=31, name="d31"),
    )
    mocker.patch("medperf.config.comms.get_experiment_aggregator", return_value=None)
    mocker.patch(
        "medperf.config.comms.get_experiment_event", return_value={"finished": True}
    )
    mocker.patch(
        "medperf.entities.aggregator.Aggregator.all",
        return_value=[TEST_AGG],
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))
    page.wait_for_presence_selector(page.SET_AGGREGATOR_FORM)
    page.wait_for_presence_selector(page.SET_PLAN_FORM)
    page.wait_for_presence_selector(page.UPDATE_PLAN_FORM)
    page.wait_for_presence_selector(page.START_EVENT_FORM)
    page.wait_for_presence_selector(page.GET_STATUS_FORM)


def test_training_details_page_non_owner(page, mocker):
    exp = TestTrainingExp(
        id=77,
        owner=2,
        name="train-77",
        data_preparation_mlcube=1,
        fl_mlcube=2,
        fl_admin_mlcube=None,
    )
    exp.plan = {"epochs": 1}
    mocker.patch("medperf.entities.training_exp.TrainingExp.get", return_value=exp)
    mocker.patch(
        "medperf.entities.cube.Cube.get",
        return_value=PREP_CUBE,
    )
    mocker.patch(
        "medperf.commands.association.utils.get_experiment_associations",
        return_value=[],
    )
    mocker.patch("medperf.config.comms.get_experiment_aggregator", return_value=None)
    mocker.patch(
        "medperf.config.comms.get_experiment_event", return_value={"finished": True}
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.SET_PLAN_FORM)


def test_training_details_set_plan_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = _base_exp(plan={})
    _mock_common(mocker, exp, aggregator=TEST_AGG)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_set_plan = mocker.patch(PATCH_ROUTE.format("SetPlan.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.set_training_plan("plan.yaml")
    page.wait_for_visibility_element(confirm_modal)

    assert page.get_text(page.CONFIRM_TEXT) == "Are you sure you want to set the training plan?"

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Setting training plan completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="set_training_plan")
    spy_set_plan.assert_called_once_with(77, "plan.yaml")
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_set_plan_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Set plan test failed"
    exp = _base_exp(plan={})
    _mock_common(mocker, exp, aggregator=TEST_AGG)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_set_plan = mocker.patch(
        PATCH_ROUTE.format("SetPlan.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.set_training_plan("plan.yaml")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while setting training plan"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="set_training_plan")
    spy_set_plan.assert_called_once_with(77, "plan.yaml")
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_update_plan_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=TEST_AGG)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_update_plan = mocker.patch(PATCH_ROUTE.format("UpdatePlan.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.update_training_plan("epochs", "5")
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to update the training plan with this field?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Updating training plan completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="update_training_plan")
    spy_update_plan.assert_called_once_with(77, "epochs", "5")
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_update_plan_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Update plan test failed"
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=TEST_AGG)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_update_plan = mocker.patch(
        PATCH_ROUTE.format("UpdatePlan.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.update_training_plan("epochs", "5")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while updating training plan"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="update_training_plan")
    spy_update_plan.assert_called_once_with(77, "epochs", "5")
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_start_event_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=TEST_AGG, event_finished=True)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_start_event = mocker.patch(PATCH_ROUTE.format("StartEvent.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.start_training_event("event1")
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to start this training event?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Starting event completed successfully"

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="start_training_event")
    spy_start_event.assert_called_once_with(77, "event1", participants_list_file=None)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_start_event_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Start event test failed"
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=TEST_AGG, event_finished=True)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_start_event = mocker.patch(
        PATCH_ROUTE.format("StartEvent.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.start_training_event("event1")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while starting event"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="start_training_event")
    spy_start_event.assert_called_once_with(77, "event1", participants_list_file=None)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_close_event_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=TEST_AGG, event_finished=False)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_close_event = mocker.patch(PATCH_ROUTE.format("CloseEvent.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.close_training_event()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to close the current training event?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Closing event completed successfully"

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="close_training_event")
    spy_close_event.assert_called_once_with(77)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_close_event_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Close event test failed"
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=TEST_AGG, event_finished=False)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_close_event = mocker.patch(
        PATCH_ROUTE.format("CloseEvent.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.close_training_event()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while closing event"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="close_training_event")
    spy_close_event.assert_called_once_with(77)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_get_experiment_status_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=TEST_AGG)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_get_status = mocker.patch(PATCH_ROUTE.format("GetExperimentStatus.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.get_experiment_status()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to get the experiment status?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Getting experiment status completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="get_training_status")
    spy_get_status.assert_called_once_with(77, silent=True)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_get_experiment_status_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Get status test failed"
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=TEST_AGG)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_get_status = mocker.patch(
        PATCH_ROUTE.format("GetExperimentStatus.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.get_experiment_status()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while getting experiment status"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="get_training_status")
    spy_get_status.assert_called_once_with(77, silent=True)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_add_aggregator_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=None)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_add_aggregator = mocker.patch(PATCH_ROUTE.format("SetAggregator.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.set_aggregator("agg")
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to set this aggregator for this training experiment?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Setting aggregator completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="set_training_aggregator")
    spy_add_aggregator.assert_called_once_with(77, TEST_AGG.id)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_add_aggregator_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Add aggregator test failed"
    exp = _base_exp()
    _mock_common(mocker, exp, aggregator=None)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_add_aggregator = mocker.patch(
        PATCH_ROUTE.format("SetAggregator.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.set_aggregator("agg")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while setting aggregator"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="set_training_aggregator")
    spy_add_aggregator.assert_called_once_with(77, TEST_AGG.id)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_approve_dataset_association_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = _base_exp()
    _mock_common(
        mocker,
        exp,
        aggregator=TEST_AGG,
        associations=[
            {"training_exp": 77, "dataset": 31, "approval_status": "PENDING", "created_at": datetime.datetime(2025, 1, 1)}
        ],
    )

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_approve = mocker.patch(PATCH_ROUTE.format("Approval.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.approve_first_pending_dataset_association()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to approve this dataset association?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Approving association completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="approve_training_dataset_association")
    spy_approve.assert_called_once_with(
        training_exp_uid=77, approval_status=Status.APPROVED, dataset_uid=31
    )
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_training_details_reject_dataset_association_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = _base_exp()
    _mock_common(
        mocker,
        exp,
        aggregator=TEST_AGG,
        associations=[
            {"training_exp": 77, "dataset": 31, "approval_status": "PENDING", "created_at": datetime.datetime(2025, 1, 1)}
        ],
    )

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_reject = mocker.patch(PATCH_ROUTE.format("Approval.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/training/ui/display/77"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.reject_first_pending_dataset_association()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to reject this dataset association?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Rejecting association completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="reject_training_dataset_association")
    spy_reject.assert_called_once_with(
        training_exp_uid=77, approval_status=Status.REJECTED, dataset_uid=31
    )
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()
