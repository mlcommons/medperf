import datetime
from unittest.mock import ANY

from medperf.tests.mocks.cube import TestCube
import pytest
from selenium.webdriver.common.by import By

from medperf.tests.mocks.dataset import TestDataset
from medperf.tests.mocks.training_exp import TestTrainingExp
from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.dataset.details_page import DatasetDetailsPage
from medperf.web_ui.tests.pages.dataset.register_page import RegDatasetPage
from medperf.web_ui.tests.unit.helpers import (
    patch_medperf_session,
    switch_to_ui_mode,
    stub_event_generator,
)
import medperf.web_ui.events as events_module

BASE_URL = tests_config.BASE_URL
PATCH_ROUTE = "medperf.web_ui.datasets.routes.{}"


def _patch_common(mocker):
    patch_medperf_session(
        mocker,
        email="training-ui-test@local",
        route_modules=("datasets",),
        with_user_object=True,
    )


def _make_dataset(**overrides):
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
    dataset.get_cc_config = lambda: overrides.get("cc_config", {})
    dataset.is_cc_configured = lambda: overrides.get("cc_configured", False)
    dataset.is_cc_initialized = lambda: overrides.get("cc_initialized", False)
    dataset.get_last_synced = lambda: overrides.get("cc_last_synced", None)
    dataset.report_path = ""
    dataset.report = {}
    dataset.generated_metadata = {}
    return dataset


@pytest.fixture
def reg_page(driver):
    return RegDatasetPage(driver)


@pytest.fixture
def details_page(driver):
    return DatasetDetailsPage(driver)


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
        "medperf.web_ui.entity_search.get_container_type",
        return_value="data-prep-container",
    )

    switch_to_ui_mode(reg_page, "training")
    reg_page.open(BASE_URL.format("/datasets/register/ui"))
    reg_page.wait_for_presence_selector(reg_page.DATA_PREP)
    assert reg_page.driver.find_elements(*reg_page.BENCHMARK) == []
    assert reg_page.get_text(reg_page.DATA_PREP_LABEL) == "Data Preparation Container"


def test_dataset_details_training_actions(details_page, mocker):
    _patch_common(mocker)
    dataset = _make_dataset(cc_initialized=True)

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


def test_dataset_details_associate_training_succeed(
    details_page, mocker, ui, patch_common, patch_task_events
):
    _patch_common(mocker)
    dataset = _make_dataset()
    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(PATCH_ROUTE.format("get_user_associations"), return_value=[])
    mocker.patch(
        "medperf.entities.training_exp.TrainingExp.all",
        return_value=[TestTrainingExp(id=55, name="tr-55", data_preparation_mlcube=1)],
    )

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_associate = mocker.patch(PATCH_ROUTE.format("AssociateTrainingDataset.run"))

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))

    confirm_modal = details_page.find(details_page.PAGE_MODAL)
    popup_modal = details_page.find(details_page.PAGE_MODAL)

    details_page.request_training_association_for_experiment("tr-55")
    details_page.wait_for_visibility_element(confirm_modal)

    assert (
        details_page.get_text(details_page.CONFIRM_TEXT)
        == "Are you sure you want to associate this dataset with this training experiment?"
    )

    details_page.confirm_run_task()
    details_page.wait_for_visibility_element(popup_modal)

    assert (
        details_page.get_text(details_page.PAGE_MODAL_TITLE)
        == "Requesting association completed successfully"
    )

    details_page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="dataset_training_association")
    spy_associate.assert_called_once_with(data_uid=31, training_exp_uid=55, approved=True)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_dataset_details_associate_training_fails(
    details_page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Associate training test failed"
    _patch_common(mocker)
    dataset = _make_dataset()
    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(PATCH_ROUTE.format("get_user_associations"), return_value=[])
    mocker.patch(
        "medperf.entities.training_exp.TrainingExp.all",
        return_value=[TestTrainingExp(id=55, name="tr-55", data_preparation_mlcube=1)],
    )

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_associate = mocker.patch(
        PATCH_ROUTE.format("AssociateTrainingDataset.run"),
        side_effect=Exception(error_msg),
    )

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))

    confirm_modal = details_page.find(details_page.PAGE_MODAL)
    error_modal = details_page.find(details_page.PAGE_MODAL)

    details_page.request_training_association_for_experiment("tr-55")
    details_page.wait_for_visibility_element(confirm_modal)
    details_page.confirm_run_task()
    details_page.wait_for_visibility_element(error_modal)
    details_page.wait_for_presence_selector(details_page.ERROR_RELOAD)

    assert details_page.get_text(details_page.PAGE_MODAL_TITLE) == (
        "Something when wrong while requesting association"
    )
    assert error_msg in details_page.get_text(details_page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*details_page.ERROR_HIDE)
    details_page.ensure_element_ready(hide_btn)
    hide_btn.click()
    details_page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="dataset_training_association")
    spy_associate.assert_called_once_with(data_uid=31, training_exp_uid=55, approved=True)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_dataset_details_start_training_succeed(
    details_page, mocker, ui, patch_common, patch_task_events
):
    _patch_common(mocker)
    dataset = _make_dataset()
    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(
        PATCH_ROUTE.format("get_user_associations"),
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

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_start_training = mocker.patch(PATCH_ROUTE.format("TrainingExecution.run"))

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))

    confirm_modal = details_page.find(details_page.PAGE_MODAL)
    popup_modal = details_page.find(details_page.PAGE_MODAL)

    details_page.start_training_for_experiment("tr-55")
    details_page.wait_for_visibility_element(confirm_modal)

    assert (
        details_page.get_text(details_page.CONFIRM_TEXT)
        == "Are you sure you want to start training for this experiment with this dataset?"
    )

    details_page.confirm_run_task()
    details_page.wait_for_visibility_element(popup_modal)

    assert details_page.get_text(details_page.PAGE_MODAL_TITLE) == "Training Ran Successfully"

    details_page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="start_training")
    spy_start_training.assert_called_once_with(training_exp_id=55, data_uid=31)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_dataset_details_start_training_fails(
    details_page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Start training test failed"
    _patch_common(mocker)
    dataset = _make_dataset()
    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(
        PATCH_ROUTE.format("get_user_associations"),
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

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_start_training = mocker.patch(
        PATCH_ROUTE.format("TrainingExecution.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))

    confirm_modal = details_page.find(details_page.PAGE_MODAL)
    error_modal = details_page.find(details_page.PAGE_MODAL)

    details_page.start_training_for_experiment("tr-55")
    details_page.wait_for_visibility_element(confirm_modal)
    details_page.confirm_run_task()
    details_page.wait_for_visibility_element(error_modal)
    details_page.wait_for_presence_selector(details_page.ERROR_RELOAD)

    assert details_page.get_text(details_page.PAGE_MODAL_TITLE) == (
        "Something went wrong while running the training"
    )
    assert error_msg in details_page.get_text(details_page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*details_page.ERROR_HIDE)
    details_page.ensure_element_ready(hide_btn)
    hide_btn.click()
    details_page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="start_training")
    spy_start_training.assert_called_once_with(training_exp_id=55, data_uid=31)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_dataset_details_edit_cc_config_succeed(
    details_page, mocker, ui, patch_common, patch_task_events
):
    _patch_common(mocker)
    dataset = _make_dataset()
    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(PATCH_ROUTE.format("get_user_associations"), return_value=[])
    mocker.patch("medperf.entities.training_exp.TrainingExp.all", return_value=[])

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_configure = mocker.patch(PATCH_ROUTE.format("DatasetConfigureForCC.run"))

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))

    confirm_modal = details_page.find(details_page.PAGE_MODAL)
    popup_modal = details_page.find(details_page.PAGE_MODAL)

    cc_values = {
        "project_id": "proj-id",
        "project_number": "proj-number",
        "bucket": "bucket-name",
        "keyring_name": "keyring",
        "key_name": "key",
        "key_location": "us",
        "wip": "wip-name",
        "wip_provider": "wip-provider",
    }
    details_page.configure_cc(cc_values)
    details_page.wait_for_visibility_element(confirm_modal)

    assert (
        details_page.get_text(details_page.CONFIRM_TEXT)
        == "Are you sure you want to edit CC configuration?"
    )

    details_page.confirm_run_task()
    details_page.wait_for_visibility_element(popup_modal)

    assert (
        details_page.get_text(details_page.PAGE_MODAL_TITLE)
        == "Updating Dataset CC configuration completed successfully"
    )

    details_page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="data_update_cc_config")
    spy_configure.assert_called_once_with(31, cc_values, {})
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_dataset_details_edit_cc_config_fails(
    details_page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Edit dataset CC config test failed"
    _patch_common(mocker)
    dataset = _make_dataset()
    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(PATCH_ROUTE.format("get_user_associations"), return_value=[])
    mocker.patch("medperf.entities.training_exp.TrainingExp.all", return_value=[])

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_configure = mocker.patch(
        PATCH_ROUTE.format("DatasetConfigureForCC.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))

    confirm_modal = details_page.find(details_page.PAGE_MODAL)
    error_modal = details_page.find(details_page.PAGE_MODAL)

    cc_values = {
        "project_id": "proj-id",
        "project_number": "proj-number",
        "bucket": "bucket-name",
        "keyring_name": "keyring",
        "key_name": "key",
        "key_location": "us",
        "wip": "wip-name",
        "wip_provider": "wip-provider",
    }
    details_page.configure_cc(cc_values)
    details_page.wait_for_visibility_element(confirm_modal)
    details_page.confirm_run_task()
    details_page.wait_for_visibility_element(error_modal)
    details_page.wait_for_presence_selector(details_page.ERROR_RELOAD)

    assert details_page.get_text(details_page.PAGE_MODAL_TITLE) == (
        "Something when wrong while updating dataset cc configuration"
    )
    assert error_msg in details_page.get_text(details_page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*details_page.ERROR_HIDE)
    details_page.ensure_element_ready(hide_btn)
    hide_btn.click()
    details_page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="data_update_cc_config")
    spy_configure.assert_called_once_with(31, cc_values, {})
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_dataset_details_sync_cc_policy_succeed(
    details_page, mocker, ui, patch_common, patch_task_events
):
    _patch_common(mocker)
    dataset = _make_dataset(cc_configured=True, cc_initialized=True)
    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(PATCH_ROUTE.format("get_user_associations"), return_value=[])
    mocker.patch("medperf.entities.training_exp.TrainingExp.all", return_value=[])

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_sync = mocker.patch(PATCH_ROUTE.format("DatasetUpdateCCPolicy.run"))

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))

    confirm_modal = details_page.find(details_page.PAGE_MODAL)
    popup_modal = details_page.find(details_page.PAGE_MODAL)

    details_page.sync_cc_policy()
    details_page.wait_for_visibility_element(confirm_modal)

    assert (
        details_page.get_text(details_page.CONFIRM_TEXT)
        == "Are you sure you want to sync CC policy?"
    )

    details_page.confirm_run_task()
    details_page.wait_for_visibility_element(popup_modal)

    assert (
        details_page.get_text(details_page.PAGE_MODAL_TITLE)
        == "Syncing CC policy completed successfully"
    )

    details_page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="data_update_cc_policy")
    spy_sync.assert_called_once_with(31)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_dataset_details_sync_cc_policy_fails(
    details_page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Sync dataset CC policy test failed"
    _patch_common(mocker)
    dataset = _make_dataset(cc_configured=True, cc_initialized=True)
    mocker.patch("medperf.entities.dataset.Dataset.get", return_value=dataset)
    mocker.patch(
        "medperf.entities.cube.Cube.get", return_value=TestCube(id=1, name="prep")
    )
    mocker.patch(PATCH_ROUTE.format("get_user_associations"), return_value=[])
    mocker.patch("medperf.entities.training_exp.TrainingExp.all", return_value=[])

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_sync = mocker.patch(
        PATCH_ROUTE.format("DatasetUpdateCCPolicy.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(details_page, "training")
    details_page.open(BASE_URL.format("/datasets/ui/display/31"))

    confirm_modal = details_page.find(details_page.PAGE_MODAL)
    error_modal = details_page.find(details_page.PAGE_MODAL)

    details_page.sync_cc_policy()
    details_page.wait_for_visibility_element(confirm_modal)
    details_page.confirm_run_task()
    details_page.wait_for_visibility_element(error_modal)
    details_page.wait_for_presence_selector(details_page.ERROR_RELOAD)

    assert details_page.get_text(details_page.PAGE_MODAL_TITLE) == (
        "Something when wrong while syncing cc policy"
    )
    assert error_msg in details_page.get_text(details_page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*details_page.ERROR_HIDE)
    details_page.ensure_element_ready(hide_btn)
    hide_btn.click()
    details_page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="data_update_cc_policy")
    spy_sync.assert_called_once_with(31)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()
