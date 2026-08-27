from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.asset.register_page import RegAssetPage
from medperf.web_ui.tests.unit.helpers import stub_event_generator
from medperf.tests.mocks.asset import TestAsset
from medperf.tests.mocks.model import TestModel

import pytest
from unittest.mock import ANY
import medperf.web_ui.events as events_module

BASE_URL = tests_config.BASE_URL
PATCH_ROUTE = "medperf.web_ui.assets.routes.{}"


def _mock_asset_redirect_cascade(mocker, asset_id, model_id):
    asset = TestAsset(id=asset_id, name="test-asset")
    model = mocker.MagicMock()
    model.id = model_id
    mocker.patch("medperf.entities.asset.Asset.get", return_value=asset)
    mocker.patch("medperf.entities.model.Model.get_by_asset", return_value=model)


@pytest.fixture
def page(driver):
    return RegAssetPage(driver)


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


def test_asset_register_page_content(page):
    page.open(BASE_URL.format("/assets/register/ui"))

    page.wait_for_presence_selector(page.FORM)
    page.wait_for_presence_selector(page.NAME)
    page.wait_for_presence_selector(page.LOCAL_RADIO)
    page.wait_for_presence_selector(page.REMOTE_RADIO)
    page.wait_for_presence_selector(page.REGISTER)

    assert page.get_attribute(page.REGISTER, "disabled") == "true"


def test_asset_register_local_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_register = mocker.patch(PATCH_ROUTE.format("SubmitAsset.run"), return_value=7)
    # On success the reload modal auto-navigates to /assets/ui/display/7,
    # which itself immediately redirects to the owning model's page - mock
    # that whole cascade so the redirect resolves instead of 500ing.
    _mock_asset_redirect_cascade(mocker, asset_id=7, model_id=42)

    page.open(BASE_URL.format("/assets/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.register_local_asset("test-asset", "/path/to/asset")
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to register this asset?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering asset completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="asset_registration")
    spy_register.assert_called_once_with(
        "test-asset", asset_path="/path/to/asset", asset_url=None, operational=True
    )
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_asset_register_local_fails(page, mocker, ui, patch_common, patch_task_events):
    error_msg = "Asset registration test failed"
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_register = mocker.patch(
        PATCH_ROUTE.format("SubmitAsset.run"), side_effect=Exception(error_msg)
    )

    page.open(BASE_URL.format("/assets/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.register_local_asset("test-asset", "/path/to/asset")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something when wrong while registering asset"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    spy_init.assert_called_once_with(ANY, task_name="asset_registration")
    spy_register.assert_called_once_with(
        "test-asset", asset_path="/path/to/asset", asset_url=None, operational=True
    )
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_asset_register_remote_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_register = mocker.patch(PATCH_ROUTE.format("SubmitAsset.run"), return_value=7)
    _mock_asset_redirect_cascade(mocker, asset_id=7, model_id=42)

    page.open(BASE_URL.format("/assets/register/ui"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.register_remote_asset("test-asset", "https://example.com/asset.tar.gz")
    page.wait_for_visibility_element(confirm_modal)

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering asset completed successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_register.assert_called_once_with(
        "test-asset",
        asset_path=None,
        asset_url="https://example.com/asset.tar.gz",
        operational=True,
    )


def test_asset_detail_redirects_to_model(page, mocker):
    _mock_asset_redirect_cascade(mocker, asset_id=9, model_id=42)
    # page.open() waits for the final destination's navbar, so the full
    # redirect chain has to resolve: /assets/ui/display/9 ->
    # /models/ui/display/42, which itself needs Model.get(42) to render.
    mocker.patch(
        "medperf.entities.model.Model.get",
        return_value=TestModel(id=42, owner=1),
    )
    mocker.patch(
        "medperf.entities.model.Model.get_benchmarks_associations", return_value=[]
    )
    mocker.patch("medperf.entities.benchmark.Benchmark.all", return_value=[])
    mocker.patch("medperf.entities.cube.Cube.is_encrypted", return_value=False)
    mocker.patch(
        "medperf.web_ui.models.routes.get_medperf_user_data",
        return_value={"id": 1, "email": "test@example.com"},
    )

    page.open(BASE_URL.format("/assets/ui/display/9"))

    assert page.current_url == BASE_URL.format("/models/ui/display/42")
