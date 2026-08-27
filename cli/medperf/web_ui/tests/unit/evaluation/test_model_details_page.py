from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.model.details_page import ModelDetailsPage
from medperf.web_ui.tests.unit.helpers import stub_event_generator

import datetime

import pytest
from unittest.mock import ANY
from medperf.tests.mocks.model import TestModel
import medperf.web_ui.events as events_module

BASE_URL = tests_config.BASE_URL

PATCH_MODEL_GET = "medperf.entities.model.Model.get"
PATCH_MODEL_GET_BMK_ASSOCS = "medperf.entities.model.Model.get_benchmarks_associations"
PATCH_BENCHMARK_ALL = "medperf.entities.benchmark.Benchmark.all"
PATCH_CUBE_IS_ENCRYPTED = "medperf.entities.cube.Cube.is_encrypted"
PATCH_GET_MEDPERF_USER_DATA = "medperf.web_ui.models.routes.get_medperf_user_data"
PATCH_ROUTE = "medperf.web_ui.models.routes.{}"
PATCH_CHECK_ACCESS = "medperf.web_ui.models.routes.check_access_to_container"

MODEL_ID = 20
MODEL_NAME = "test_model"
MODEL_OWNER = 1


def _make_model(**overrides):
    defaults = {
        "id": MODEL_ID,
        "name": MODEL_NAME,
        "owner": MODEL_OWNER,
        "state": "OPERATION",
        "is_valid": True,
        "created_at": datetime.datetime(2025, 10, 15, 12, 0, 0),
        "modified_at": datetime.datetime(2025, 10, 17, 12, 0, 0),
    }
    defaults.update(overrides)
    return TestModel(**defaults)


def _make_cc_initialized_model(**overrides):
    defaults = {"user_metadata": {"cc": {"config": {"project_id": "p"}, "initialized": True}}}
    defaults.update(overrides)
    return _make_model(**defaults)


@pytest.fixture
def model_mock(mocker):
    m = _make_model()
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=False)
    yield m


@pytest.fixture
def page(driver):
    return ModelDetailsPage(driver)


def _patch_user(mocker, user_id: int):
    mocker.patch(PATCH_GET_MEDPERF_USER_DATA, return_value={"id": user_id})


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


@pytest.mark.parametrize("user_id", [MODEL_OWNER, MODEL_OWNER + 1])
def test_model_details_common_content(page, mocker, model_mock, user_id):
    _patch_user(mocker, user_id)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    assert page.get_text(page.HEADER) == MODEL_NAME
    assert page.get_text(page.DETAILS_HEADING) == "Details"

    assert page.get_text(page.MODEL_ID_LABEL) == "Model ID"
    assert page.get_text(page.MODEL_ID_VALUE) == str(MODEL_ID)

    assert page.get_text(page.MANIFEST_LABEL) == "Container Manifest"
    assert (
        page.get_text(page.MANIFEST_YAML_BTN)
        == "Click to display Container Configuration"
    )

    assert page.get_text(page.PARAMETERS_LABEL) == "Parameters"
    assert page.get_text(page.PARAMETERS_YAML_BTN) == "Click to display Parameters"

    assert page.get_text(page.ADDITIONAL_LABEL) == "Additional Files"
    assert page.get_text(page.ADDITIONAL_NA) == "Not Available"

    assert page.get_text(page.OWNER_LABEL) == "Owner"
    if user_id == MODEL_OWNER:
        assert page.get_text(page.OWNER_VALUE) == "You"
    else:
        assert page.get_text(page.OWNER_VALUE) == str(MODEL_OWNER)

    model_created = page.get_attribute(page.CREATED, "data-date")
    assert page.get_text(page.CREATED_LABEL) == "Created"
    assert (
        datetime.datetime.strptime(model_created, "%Y-%m-%d %H:%M:%S")
        == model_mock.created_at
    )

    model_modified = page.get_attribute(page.MODIFIED, "data-date")
    assert page.get_text(page.MODIFIED_LABEL) == "Modified"
    assert (
        datetime.datetime.strptime(model_modified, "%Y-%m-%d %H:%M:%S")
        == model_mock.modified_at
    )


def test_model_details_backend_calls(page, mocker):
    m = _make_model()
    spy_get = mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=False)
    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    spy_get.assert_called_once_with(MODEL_ID, valid_only=False)


@pytest.mark.parametrize("user_id", [MODEL_OWNER, MODEL_OWNER + 1])
@pytest.mark.parametrize("state", ["OPERATION", "DEVELOPMENT"])
def test_model_details_state(page, mocker, user_id, state):
    m = _make_model(state=state)
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=False)
    _patch_user(mocker, user_id)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    badges = page.driver.find_elements(*page.STATE_BADGES)
    assert len(badges) >= 1
    state_text = badges[0].text
    if state == "OPERATION":
        assert state_text == "OPERATIONAL"
    else:
        assert state_text == state


@pytest.mark.parametrize("user_id", [MODEL_OWNER, MODEL_OWNER + 1])
@pytest.mark.parametrize("is_valid", [True, False])
def test_model_details_validity(page, mocker, user_id, is_valid):
    m = _make_model(is_valid=is_valid)
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=False)
    _patch_user(mocker, user_id)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    badges = page.driver.find_elements(*page.STATE_BADGES)
    assert len(badges) >= 2
    valid_el = badges[1]
    if is_valid:
        assert valid_el.text == "VALID"
    else:
        assert valid_el.text == "INVALID"


def test_model_details_parameters_not_available(page, mocker, model_mock):
    model_mock.container.parameters_config = None
    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    assert page.get_text(page.PARAMETERS_NA) == "Not Available"


def test_model_details_invalid_card_when_invalid(page, mocker):
    m = _make_model(is_valid=False)
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=False)
    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    detail_card = page.driver.find_element("css selector", "div.invalid-card")
    assert detail_card is not None


def test_model_details_asset_branch_downloadable(page, mocker):
    m = _make_model(
        type="ASSET",
        container=None,
        asset={
            "name": "test_asset",
            "state": "OPERATION",
            "asset_hash": "abc123",
            "asset_url": "http://test.com/asset.tar.gz",
        },
    )
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    assert page.get_text(page.ASSET_LABEL) == "Asset"
    link = page.find(page.ASSET_LINK)
    assert link.get_attribute("href") == "http://test.com/asset.tar.gz"
    assert link.get_attribute("target") == "_blank"
    assert page.get_text(page.ASSET_HASH_LABEL) == "Asset Hash"
    assert page.get_text(page.ASSET_HASH) == "abc123"


def test_model_details_asset_branch_local(page, mocker):
    m = _make_model(
        type="ASSET",
        container=None,
        asset={
            "name": "test_asset",
            "state": "OPERATION",
            "asset_hash": "abc123",
            "asset_url": "local",
        },
    )
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    assert page.get_text(page.ASSET_LOCAL) == "This asset is local"


def test_model_details_access_pending_for_non_owner(page, mocker):
    m = _make_model()
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=True)
    mocker.patch(
        PATCH_CHECK_ACCESS, return_value={"has_access": False, "reason": "test reason"}
    )
    _patch_user(mocker, MODEL_OWNER + 1)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    assert page.get_text(page.ACCESS_LABEL) == "Access"
    assert page.get_text(page.ACCESS_PENDING) == "Access Pending"


def test_model_details_access_granted_for_non_owner(page, mocker):
    m = _make_model()
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=True)
    mocker.patch(PATCH_CHECK_ACCESS, return_value={"has_access": True, "reason": ""})
    _patch_user(mocker, MODEL_OWNER + 1)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    assert page.get_text(page.ACCESS_LABEL) == "Access"
    assert page.get_text(page.ACCESS_GRANTED) == "Access Granted"


def test_model_details_associate_succeed(
    page, mocker, ui, model_mock, patch_common, patch_task_events
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_associate = mocker.patch(PATCH_ROUTE.format("AssociateModel.run"))

    benchmark = mocker.MagicMock()
    benchmark.id = 5
    benchmark.name = "test_benchmark"
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[benchmark])

    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.request_association()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to request model association with this benchmark?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Requesting model association completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="model_association")
    spy_associate.assert_called_once_with(model_uid=MODEL_ID, benchmark_uid=5)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_model_details_associate_fails(
    page, mocker, ui, model_mock, patch_common, patch_task_events
):
    error_msg = "Model association test failed"
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_associate = mocker.patch(
        PATCH_ROUTE.format("AssociateModel.run"), side_effect=Exception(error_msg)
    )

    benchmark = mocker.MagicMock()
    benchmark.id = 5
    benchmark.name = "test_benchmark"
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[benchmark])

    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.request_association()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while requesting model association"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="model_association")
    spy_associate.assert_called_once_with(model_uid=MODEL_ID, benchmark_uid=5)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


CC_VALUES = {
    "project_id": "proj-id",
    "project_number": "proj-number",
    "bucket": "bucket-name",
    "keyring_name": "keyring",
    "key_name": "key",
    "key_location": "us",
    "wip": "wip-name",
    "wip_provider": "wip-provider",
}


def test_model_details_edit_cc_config_succeed(
    page, mocker, ui, model_mock, patch_common, patch_task_events
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_configure = mocker.patch(PATCH_ROUTE.format("ModelConfigureForCC.run"))

    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.configure_cc(CC_VALUES)
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to edit CC configuration?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "CC Configuration Edited Successfully"

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="model_update_cc_config")
    spy_configure.assert_called_once_with(MODEL_ID, CC_VALUES, {})
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_model_details_edit_cc_config_fails(
    page, mocker, ui, model_mock, patch_common, patch_task_events
):
    error_msg = "Edit CC config test failed"
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_configure = mocker.patch(
        PATCH_ROUTE.format("ModelConfigureForCC.run"), side_effect=Exception(error_msg)
    )

    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.configure_cc(CC_VALUES)
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Failed to Edit CC Configuration"
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="model_update_cc_config")
    spy_configure.assert_called_once_with(MODEL_ID, CC_VALUES, {})
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_model_details_sync_cc_policy_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    m = _make_cc_initialized_model()
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=False)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_sync = mocker.patch(PATCH_ROUTE.format("ModelUpdateCCPolicy.run"))

    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.sync_cc_policy()
    page.wait_for_visibility_element(confirm_modal)

    assert page.get_text(page.CONFIRM_TEXT) == "Are you sure you want to sync CC policy?"

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "CC Policy Synced Successfully"

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="model_update_cc_policy")
    spy_sync.assert_called_once_with(MODEL_ID)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_model_details_sync_cc_policy_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Sync CC policy test failed"
    m = _make_cc_initialized_model()
    mocker.patch(PATCH_MODEL_GET, return_value=m)
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[])
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[])
    mocker.patch(PATCH_CUBE_IS_ENCRYPTED, return_value=False)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_sync = mocker.patch(
        PATCH_ROUTE.format("ModelUpdateCCPolicy.run"), side_effect=Exception(error_msg)
    )

    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.sync_cc_policy()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Failed to Sync CC Policy"
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="model_update_cc_policy")
    spy_sync.assert_called_once_with(MODEL_ID)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_model_details_associated_benchmarks_section(page, mocker, model_mock):
    assoc = {
        "benchmark": 5,
        "model": MODEL_ID,
        "approval_status": "PENDING",
    }
    mocker.patch(PATCH_MODEL_GET_BMK_ASSOCS, return_value=[assoc])
    benchmark = mocker.MagicMock()
    benchmark.id = 5
    benchmark.name = "test_benchmark"
    mocker.patch(PATCH_BENCHMARK_ALL, return_value=[benchmark])
    _patch_user(mocker, MODEL_OWNER)

    page.open(BASE_URL.format(f"/models/ui/display/{MODEL_ID}"))

    assert page.get_text(page.ASSOCIATIONS_BTN) == "Associated Benchmarks\n1"
