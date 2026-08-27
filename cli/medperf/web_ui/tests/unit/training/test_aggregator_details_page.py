import datetime
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock

from medperf.tests.mocks.training_exp import TestTrainingExp
import pytest
from selenium.common.exceptions import NoSuchElementException

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.aggregator.details_page import AggregatorDetailsPage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode, stub_event_generator
import medperf.web_ui.events as events_module

BASE_URL = tests_config.BASE_URL
PATCH_ROUTE = "medperf.web_ui.aggregators.routes.{}"

TEST_TRAINING_EXPS = [TestTrainingExp(id=77, name="tr-77")]


def _make_agg(**overrides):
    defaults = dict(
        id=9,
        name="agg-9",
        owner=1,
        address="127.0.0.1",
        port=7000,
        admin_port=7001,
        created_at=datetime.datetime(2026, 1, 1),
        modified_at=datetime.datetime(2026, 1, 2),
        get_training_experiments=lambda: [],
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture(autouse=True)
def patch_login(mocker):
    mocker.patch(
        "medperf.web_ui.aggregators.routes.get_medperf_user_data",
        return_value={"id": 1, "email": "training-ui-test@local"},
    )
    mocker.patch(
        "medperf.web_ui.common.read_user_account",
        return_value={"email": "training-ui-test@local"},
    )
    mocker.patch(
        "medperf.web_ui.common.get_medperf_user_data",
        return_value={"id": 1, "email": "training-ui-test@local"},
    )


@pytest.fixture
def page(driver):
    return AggregatorDetailsPage(driver)


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


def test_aggregator_details_page_common_content(page, mocker):
    agg = SimpleNamespace(
        id=9,
        name="agg-9",
        owner=1,
        address="127.0.0.1",
        port=7000,
        admin_port=7001,
        created_at=datetime.datetime(2026, 1, 1),
        modified_at=datetime.datetime(2026, 1, 2),
        get_training_experiments=lambda: TEST_TRAINING_EXPS,
    )
    mocker.patch("medperf.entities.aggregator.Aggregator.get", return_value=agg)
    mocker.patch("medperf.entities.ca.CA.get", return_value=MagicMock(id=1))
    mocker.patch("medperf.web_ui.aggregators.routes.os.path.exists", return_value=False)

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui/display/9"))

    assert page.get_text(page.HEADER) == "agg-9"
    assert page.get_text(page.DETAILS_HEADING) == "Details"
    assert page.get_text(page.ID_LABEL) == "Aggregator ID"
    assert page.get_text(page.ID) == "9"
    assert page.get_text(page.OWNER_LABEL) == "Owner"
    assert page.get_text(page.ADDRESS_LABEL) == "Address"
    assert page.get_text(page.ADDRESS) == "127.0.0.1"
    assert page.get_text(page.PORT_LABEL) == "Port"
    assert page.get_text(page.PORT) == "7000"
    assert page.get_text(page.ADMIN_PORT_LABEL) == "Admin Port"
    assert page.get_text(page.ADMIN_PORT) == "7001"
    assert page.get_text(page.EXPERIMENTS_HEADING) == "Training experiments"
    assert page.get_text(page.ACTIONS_HEADING) == "Actions"
    page.wait_for_presence_selector(page.GET_CERT_FORM)
    page.wait_for_presence_selector(page.START_FORM)
    page.wait_for_presence_selector(page.STOP_BTN)


def test_aggregator_details_page_non_owner_content(page, mocker):
    agg = SimpleNamespace(
        id=9,
        name="agg-9",
        owner=2,
        address="127.0.0.1",
        port=7000,
        admin_port=7001,
        created_at=datetime.datetime(2026, 1, 1),
        modified_at=datetime.datetime(2026, 1, 2),
        get_training_experiments=lambda: [],
    )
    mocker.patch("medperf.entities.aggregator.Aggregator.get", return_value=agg)

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui/display/9"))

    with pytest.raises(NoSuchElementException):
        page.driver.find_element(*page.ACTIONS_HEADING)


def test_aggregator_details_get_server_certificate_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    agg = _make_agg()
    mocker.patch("medperf.entities.aggregator.Aggregator.get", return_value=agg)
    mocker.patch("medperf.web_ui.aggregators.routes.os.path.exists", return_value=False)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_get_cert = mocker.patch(PATCH_ROUTE.format("GetServerCertificate.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui/display/9"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.get_server_certificate()
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to get the server certificate for this aggregator?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Server Certificate Retrieved Successfully"
    )

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="aggregator_get_server_cert")
    spy_get_cert.assert_called_once_with(aggregator_id=9)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_aggregator_details_get_server_certificate_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Get server certificate test failed"
    agg = _make_agg()
    mocker.patch("medperf.entities.aggregator.Aggregator.get", return_value=agg)
    mocker.patch("medperf.web_ui.aggregators.routes.os.path.exists", return_value=False)

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_get_cert = mocker.patch(
        PATCH_ROUTE.format("GetServerCertificate.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui/display/9"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.get_server_certificate()
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Failed to Get Server Certificate"
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="aggregator_get_server_cert")
    spy_get_cert.assert_called_once_with(aggregator_id=9)
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_aggregator_details_run_aggregator_succeed(
    page, mocker, ui, patch_common, patch_task_events
):
    exp = TestTrainingExp(id=77, name="tr-77")
    agg = _make_agg(get_training_experiments=lambda: [exp])
    mocker.patch("medperf.entities.aggregator.Aggregator.get", return_value=agg)
    mocker.patch("medperf.entities.ca.CA.get", return_value=MagicMock(id=1))
    mocker.patch("medperf.web_ui.aggregators.routes.os.path.exists", return_value=True)
    mocker.patch("medperf.entities.training_exp.TrainingExp.all", return_value=[exp])

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_run = mocker.patch(PATCH_ROUTE.format("StartAggregator.run"))

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui/display/9"))

    confirm_modal = page.find(page.PAGE_MODAL)
    popup_modal = page.find(page.PAGE_MODAL)

    page.run_aggregator_for_experiment("tr-77", publish_on="0.0.0.0")
    page.wait_for_visibility_element(confirm_modal)

    assert (
        page.get_text(page.CONFIRM_TEXT)
        == "Are you sure you want to run the aggregator for the selected training experiment?"
    )

    page.confirm_run_task()
    page.wait_for_visibility_element(popup_modal)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Aggregator Ran Successfully"

    page.wait_for_staleness_element(popup_modal)

    spy_init.assert_called_once_with(ANY, task_name="start_aggregator")
    spy_run.assert_called_once_with(training_exp_id=77, publish_on="0.0.0.0")
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()


def test_aggregator_details_run_aggregator_fails(
    page, mocker, ui, patch_common, patch_task_events
):
    error_msg = "Run aggregator test failed"
    exp = TestTrainingExp(id=77, name="tr-77")
    agg = _make_agg(get_training_experiments=lambda: [exp])
    mocker.patch("medperf.entities.aggregator.Aggregator.get", return_value=agg)
    mocker.patch("medperf.entities.ca.CA.get", return_value=MagicMock(id=1))
    mocker.patch("medperf.web_ui.aggregators.routes.os.path.exists", return_value=True)
    mocker.patch("medperf.entities.training_exp.TrainingExp.all", return_value=[exp])

    spy_init, spy_reset, spy_notifs = patch_common
    spy_event_gen, spy_task_id = patch_task_events
    spy_run = mocker.patch(
        PATCH_ROUTE.format("StartAggregator.run"), side_effect=Exception(error_msg)
    )

    switch_to_ui_mode(page, "training")
    page.open(BASE_URL.format("/aggregators/ui/display/9"))

    confirm_modal = page.find(page.PAGE_MODAL)
    error_modal = page.find(page.PAGE_MODAL)

    page.run_aggregator_for_experiment("tr-77", publish_on="0.0.0.0")
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(error_modal)
    page.wait_for_presence_selector(page.ERROR_RELOAD)

    assert page.get_text(page.PAGE_MODAL_TITLE) == (
        "Something went wrong while running the aggregator"
    )
    assert error_msg in page.get_text(page.ERROR_TEXT)

    hide_btn = error_modal.find_element(*page.ERROR_HIDE)
    page.ensure_element_ready(hide_btn)
    hide_btn.click()
    page.wait_for_invisibility_element(error_modal)

    spy_init.assert_called_once_with(ANY, task_name="start_aggregator")
    spy_run.assert_called_once_with(training_exp_id=77, publish_on="0.0.0.0")
    spy_reset.assert_called_once()
    spy_notifs.assert_called_once()
    ui.end_task.assert_called_once()
    spy_event_gen.assert_called_once_with(ANY, False)
    spy_task_id.assert_called_once()
