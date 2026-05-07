import time

import pytest

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.base_page import BasePage
from medperf.web_ui.tests.pages.security_page import SecurityPage
from medperf.web_ui.tests.pages.settings_page import SettingsPage
from medperf.web_ui.tests.pages.login_page import LoginPage

from medperf.web_ui.tests.pages.container.register_page import RegContainerPage
from medperf.web_ui.tests.pages.dataset.register_page import RegDatasetPage
from medperf.web_ui.tests.pages.dataset.details_page import DatasetDetailsPage

from medperf.web_ui.tests.pages.training.ui_page import TrainingPage
from medperf.web_ui.tests.pages.training.register_page import RegTrainingPage
from medperf.web_ui.tests.pages.training.details_page import TrainingDetailsPage

from medperf.web_ui.tests.pages.aggregator.ui_page import AggregatorsPage
from medperf.web_ui.tests.pages.aggregator.register_page import RegAggregatorPage
from medperf.web_ui.tests.pages.aggregator.details_page import AggregatorDetailsPage

from medperf.web_ui.tests.e2e.functions.common import login, logout
from medperf.web_ui.tests.e2e.helpers import (
    ensure_training_event_report_yaml_stub_dict,
    write_training_participants_yaml_for_e2e,
)

BASE_URL = tests_config.BASE_URL


def _switch_to_training_mode(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/set_mode?mode=training"))


@pytest.mark.dependency(name="training_security_token")
def test_training_security_page_token(driver, sec_token):
    page = SecurityPage(driver)
    page.open(BASE_URL.format("/"))

    assert "/security_check" in page.current_url

    old_url = page.current_url
    page.enter_token(token=sec_token)
    page.wait_for_url_change(old_url)

    assert "/security_check" not in page.current_url

    page.driver.delete_all_cookies()


@pytest.mark.dependency(
    name="training_security_url", depends=["training_security_token"]
)
def test_training_security_page_url(driver, sec_token):
    page = BasePage(driver)
    page.open(BASE_URL.format("/security_check") + f"?token={sec_token}")

    assert "/security_check" not in page.current_url


@pytest.mark.dependency(
    name="training_activate_profile", depends=["training_security_url"]
)
def test_training_activate_local_profile(driver):
    page = SettingsPage(driver)
    page.open(BASE_URL.format("/settings"))

    current_profile = page.get_text(page.CURRENT_PROFILE)
    if current_profile == tests_config.LOCAL_PROFILE:
        return

    assert page.find(page.ACTIVATE).is_enabled() is False

    page_modal = page.find(page.PAGE_MODAL)

    assert page_modal.is_displayed() is False

    page.activate_profile(profile_name=tests_config.LOCAL_PROFILE)

    page.wait_for_visibility_element(page_modal)

    assert page.is_confirmation_modal() is True
    assert "activate this profile?" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert page.get_text(page.PAGE_MODAL_TITLE) == "Profile Activated Successfully"

    page.wait_for_staleness_element(page_modal)

    assert page.get_text(page.CURRENT_PROFILE) == tests_config.LOCAL_PROFILE


@pytest.mark.dependency(
    name="training_logout_if_logged_in", depends=["training_activate_profile"]
)
def test_training_logout_if_logged_in(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    if "/medperf_login?redirected=true" not in page.current_url:
        logout(page)


@pytest.mark.dependency(
    name="training_model_login", depends=["training_logout_if_logged_in"]
)
def test_training_model_owner_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.MODEL_OWNER_EMAIL,
        training=True,
    )


@pytest.mark.dependency(name="training_register_fl", depends=["training_model_login"])
def test_training_register_fl_container(driver):
    page = RegContainerPage(driver)
    page.open(BASE_URL.format("/containers/ui"))

    old_url = page.current_url
    page.click(page.REG_CONTAINER_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.register_container(container=tests_config.TRAINING_FL, mode="training")

    old_url = page.current_url
    page.wait_for_visibility_element(page_modal)

    assert page.is_confirmation_modal() is True

    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering container completed successfully"
    )

    page.wait_for_staleness_element(page_modal)
    page.wait_for_url_change(old_url)

    assert "/containers/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="training_register_fl_admin", depends=["training_register_fl"]
)
def test_training_register_fl_admin_container(driver):
    page = RegContainerPage(driver)
    page.open(BASE_URL.format("/containers/ui"))

    old_url = page.current_url
    page.click(page.REG_CONTAINER_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.register_container(container=tests_config.TRAINING_FL_ADMIN, mode="training")

    old_url = page.current_url
    page.wait_for_visibility_element(page_modal)

    assert page.is_confirmation_modal() is True

    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering container completed successfully"
    )

    page.wait_for_staleness_element(page_modal)
    page.wait_for_url_change(old_url)

    assert "/containers/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="training_register_experiment", depends=["training_register_fl_admin"]
)
def test_training_register_experiment(driver):
    listing = TrainingPage(driver)
    listing.open(BASE_URL.format("/training/ui"))

    old_url = listing.current_url
    listing.click(listing.REG_TRAINING_BTN)
    listing.wait_for_url_change(old_url)
    listing.wait_for_presence_selector(listing.NAVBAR)

    assert "/training/register/ui" in listing.current_url

    page = RegTrainingPage(driver)
    assert page.find(page.REGISTER).is_enabled() is False

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    assert page_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.register_training(
        name=tests_config.TRAINING_EXP_NAME,
        description=tests_config.TRAINING_EXP_DESC,
        data_prep=tests_config.TRAINING_PREP_NAME,
        fl_container=tests_config.TRAINING_FL_NAME,
        fl_admin_container=tests_config.TRAINING_FL_ADMIN_NAME,
    )

    old_url = page.current_url
    page.wait_for_visibility_element(page_modal)

    assert page.is_confirmation_modal() is True
    assert "register this training experiment?" in page.get_text(page.CONFIRM_TEXT)

    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering training experiment completed successfully"
    )

    page.wait_for_staleness_element(page_modal)
    page.wait_for_url_change(old_url)

    assert "/training/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="training_model_logout", depends=["training_register_experiment"]
)
def test_training_model_logout_after_experiment(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/training/ui"))
    logout(page)


@pytest.mark.dependency(
    name="training_agg_owner_login", depends=["training_model_logout"]
)
def test_training_aggregator_owner_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.AGG_OWNER_EMAIL,
        training=True,
    )


@pytest.mark.dependency(
    name="training_register_aggregator", depends=["training_agg_owner_login"]
)
def test_training_register_aggregator(driver):
    listing = AggregatorsPage(driver)
    listing.open(BASE_URL.format("/aggregators/ui"))

    old_url = listing.current_url
    listing.click(listing.REG_AGG_BTN)
    listing.wait_for_url_change(old_url)
    listing.wait_for_presence_selector(listing.NAVBAR)

    assert "/aggregators/register/ui" in listing.current_url

    page = RegAggregatorPage(driver)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.register_aggregator(
        name=tests_config.TRAINING_AGG_NAME,
        address=tests_config.HOST,
        port=tests_config.TRAINING_AGG_PORT,
        admin_port=tests_config.TRAINING_AGG_ADMIN_PORT,
        aggregation_mlcube=tests_config.TRAINING_FL_NAME,
    )

    old_url = page.current_url
    page.wait_for_visibility_element(page_modal)

    assert page.is_confirmation_modal() is True

    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering aggregator completed successfully"
    )

    page.wait_for_staleness_element(page_modal)
    page.wait_for_url_change(old_url)

    assert "/aggregators/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="training_agg_logout", depends=["training_register_aggregator"]
)
def test_training_aggregator_owner_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/aggregators/ui"))
    logout(page)


@pytest.mark.dependency(name="training_model_relogin1", depends=["training_agg_logout"])
def test_training_model_owner_relogin(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.MODEL_OWNER_EMAIL,
        training=True,
    )


@pytest.mark.dependency(
    name="training_set_aggregator", depends=["training_model_relogin1"]
)
def test_training_set_aggregator(driver):
    listing = TrainingPage(driver)
    listing.open(BASE_URL.format("/training/ui"))
    listing.open_experiment_by_name(tests_config.TRAINING_EXP_NAME)

    page = TrainingDetailsPage(driver)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    assert page_modal.is_displayed() is False
    assert panel.is_displayed() is False
    assert prompt_container.is_displayed() is False

    page.set_aggregator(
        tests_config.TRAINING_AGG_NAME,
        tests_config.HOST,
        tests_config.TRAINING_AGG_PORT,
    )

    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Setting aggregator completed successfully"
    )
    page.wait_for_staleness_element(page_modal)

    assert "/training/ui/display/1" in page.current_url


@pytest.mark.dependency(name="training_set_plan", depends=["training_set_aggregator"])
def test_training_set_plan(driver):
    listing = TrainingPage(driver)
    listing.open(BASE_URL.format("/training/ui"))
    listing.open_experiment_by_name(tests_config.TRAINING_EXP_NAME)

    page = TrainingDetailsPage(driver)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    assert page_modal.is_displayed() is False
    assert panel.is_displayed() is False
    assert prompt_container.is_displayed() is False

    page.set_training_plan(tests_config.TRAINING_PLAN_PATH)

    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Setting training plan completed successfully"
    )
    page.wait_for_staleness_element(page_modal)

    assert "/training/ui/display/" in page.current_url


@pytest.mark.dependency(name="training_start_event", depends=["training_set_plan"])
def test_training_start_event(driver):
    participants_list_path = write_training_participants_yaml_for_e2e()

    listing = TrainingPage(driver)
    listing.open(BASE_URL.format("/training/ui"))
    listing.open_experiment_by_name(tests_config.TRAINING_EXP_NAME)

    page = TrainingDetailsPage(driver)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    assert page_modal.is_displayed() is False
    assert panel.is_displayed() is False
    assert prompt_container.is_displayed() is False

    page.start_training_event(
        event_name=tests_config.TRAINING_EVENT_NAME,
        participants_list_path=participants_list_path,
    )

    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE) == "Starting event completed successfully"
    )
    page.wait_for_staleness_element(page_modal)

    assert "/training/ui/display/1" in page.current_url


@pytest.mark.dependency(name="training_model_logout1", depends=["training_set_plan"])
def test_training_model_logout1(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/training/ui"))
    logout(page)


@pytest.mark.dependency(name="training_data1_login", depends=["training_model_logout1"])
def test_training_data_owner_1_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.DSET_OWNER_EMAIL,
        training=True,
    )


@pytest.mark.dependency(name="training_data1_dataset", depends=["training_data1_login"])
def test_training_data_owner_1_register_dataset(driver):
    from helpers import prepare_chestxray_train_sample_data

    prepare_chestxray_train_sample_data()
    page = RegDatasetPage(driver)
    page.open(BASE_URL.format("/datasets/ui"))

    old_url = page.current_url
    page.click(page.REG_DSET_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    page_modal = page.find(page.PAGE_MODAL)
    text_container = page.find(page.TEXT_CONTAINER)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.register_dataset_training(
        data_prep_name=tests_config.TRAINING_PREP_NAME,
        name=tests_config.TRAINING_DATASET1_NAME,
        description=tests_config.TRAINING_DATASET1_DESC,
        location=tests_config.TRAINING_DATASET1_LOCATION,
        data_path=tests_config.TRAINING_DATASET1_DATA_PATH,
        labels_path=tests_config.TRAINING_DATASET1_LABELS_PATH,
    )

    old_url = page.current_url
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()

    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert text_container.is_displayed() is True
    assert prompt_container.is_displayed() is True
    page.click(page.RESPOND_YES)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering dataset completed successfully"
    )

    page.wait_for_staleness_element(page_modal)
    page.wait_for_url_change(old_url)
    assert "/datasets/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="training_data1_prepare", depends=["training_data1_dataset"]
)
def test_training_data_owner_1_prepare(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.TRAINING_DATASET1_NAME)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.prepare_dataset()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Preparing dataset completed successfully"
    )
    page.wait_for_staleness_element(page_modal)
    page.wait_for_presence_selector(page.PREPARED_TEXT)


@pytest.mark.dependency(
    name="training_data1_operational", depends=["training_data1_prepare"]
)
def test_training_data_owner_1_set_operational(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.TRAINING_DATASET1_NAME)
    page_modal = page.find(page.PAGE_MODAL)
    text_container = page.find(page.TEXT_CONTAINER)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.set_operational()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()

    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert text_container.is_displayed() is True
    assert prompt_container.is_displayed() is True
    page.click(page.RESPOND_YES)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Setting dataset to operational completed successfully"
    )
    page.wait_for_staleness_element(page_modal)
    page.wait_for_presence_selector(page.SET_OPERATIONAL_TEXT)


@pytest.mark.dependency(
    name="training_data1_associate", depends=["training_data1_operational"]
)
def test_training_data_owner_1_associate(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.TRAINING_DATASET1_NAME)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.request_training_association_for_experiment(tests_config.TRAINING_EXP_NAME)

    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    assert "associate this dataset with this training experiment?" in page.get_text(
        page.CONFIRM_TEXT
    )
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Requesting association completed successfully"
    )
    page.wait_for_staleness_element(page_modal)


@pytest.mark.dependency(
    name="training_data1_cert", depends=["training_data1_associate"]
)
def test_training_data_owner_1_certificate(driver):
    page = SettingsPage(driver)
    page.open(BASE_URL.format("/settings"))

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.get_client_certificate()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Getting Client Certificate completed successfully"
    )
    page.wait_for_staleness_element(page_modal)

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.submit_certificate()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)
    assert prompt_container.is_displayed() is True
    page.click(page.RESPOND_YES)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Submitting Client Certificate completed successfully"
    )
    page.wait_for_staleness_element(page_modal)


@pytest.mark.dependency(name="training_data1_logout", depends=["training_data1_cert"])
def test_training_data_owner_1_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/datasets/ui"))
    logout(page)


@pytest.mark.dependency(name="training_data2_login", depends=["training_data1_logout"])
def test_training_data_owner_2_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.DSET_OWNER2_EMAIL,
        training=True,
    )


@pytest.mark.dependency(name="training_data2_dataset", depends=["training_data2_login"])
def test_training_data_owner_2_register_dataset(driver):
    page = RegDatasetPage(driver)
    page.open(BASE_URL.format("/datasets/ui"))

    old_url = page.current_url
    page.click(page.REG_DSET_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    page_modal = page.find(page.PAGE_MODAL)
    text_container = page.find(page.TEXT_CONTAINER)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.register_dataset_training(
        data_prep_name=tests_config.TRAINING_PREP_NAME,
        name=tests_config.TRAINING_DATASET2_NAME,
        description=tests_config.TRAINING_DATASET2_DESC,
        location=tests_config.TRAINING_DATASET2_LOCATION,
        data_path=tests_config.TRAINING_DATASET2_DATA_PATH,
        labels_path=tests_config.TRAINING_DATASET2_LABELS_PATH,
    )

    old_url = page.current_url
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()

    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert text_container.is_displayed() is True
    assert prompt_container.is_displayed() is True
    page.click(page.RESPOND_YES)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Registering dataset completed successfully"
    )

    page.wait_for_staleness_element(page_modal)
    page.wait_for_url_change(old_url)
    assert "/datasets/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="training_data2_prepare", depends=["training_data2_dataset"]
)
def test_training_data_owner_2_prepare(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.TRAINING_DATASET2_NAME)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.prepare_dataset()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Preparing dataset completed successfully"
    )
    page.wait_for_staleness_element(page_modal)
    page.wait_for_presence_selector(page.PREPARED_TEXT)


@pytest.mark.dependency(
    name="training_data2_operational", depends=["training_data2_prepare"]
)
def test_training_data_owner_2_set_operational(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.TRAINING_DATASET2_NAME)
    page_modal = page.find(page.PAGE_MODAL)
    text_container = page.find(page.TEXT_CONTAINER)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.set_operational()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()

    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert text_container.is_displayed() is True
    assert prompt_container.is_displayed() is True
    page.click(page.RESPOND_YES)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Setting dataset to operational completed successfully"
    )
    page.wait_for_staleness_element(page_modal)
    page.wait_for_presence_selector(page.SET_OPERATIONAL_TEXT)


@pytest.mark.dependency(
    name="training_data2_associate", depends=["training_data2_operational"]
)
def test_training_data_owner_2_associate(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.TRAINING_DATASET2_NAME)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.request_training_association_for_experiment(tests_config.TRAINING_EXP_NAME)

    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Requesting association completed successfully"
    )
    page.wait_for_staleness_element(page_modal)


@pytest.mark.dependency(
    name="training_data2_cert", depends=["training_data2_associate"]
)
def test_training_data_owner_2_certificate(driver):
    page = SettingsPage(driver)
    page.open(BASE_URL.format("/settings"))

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.get_client_certificate()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Getting Client Certificate completed successfully"
    )
    page.wait_for_staleness_element(page_modal)

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.submit_certificate()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)
    assert prompt_container.is_displayed() is True
    page.click(page.RESPOND_YES)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Submitting Client Certificate completed successfully"
    )
    page.wait_for_staleness_element(page_modal)


@pytest.mark.dependency(name="training_data2_logout", depends=["training_data2_cert"])
def test_training_data_owner_2_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/datasets/ui"))
    logout(page)


@pytest.mark.dependency(name="training_model_login1", depends=["training_data2_logout"])
def test_training_model_owner_approve_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.MODEL_OWNER_EMAIL,
        training=True,
    )


@pytest.mark.dependency(
    name="training_approve_datasets", depends=["training_model_login1"]
)
def test_training_model_owner_approve_dataset_associations(driver):
    # As the associations are automatically approved (owners are in the participants list) - we skip this
    return
    listing = TrainingPage(driver)
    listing.open(BASE_URL.format("/training/ui"))
    listing.open_experiment_by_name(tests_config.TRAINING_EXP_NAME)

    page = TrainingDetailsPage(driver)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    for _ in range(2):
        page.approve_first_pending_dataset_association()
        page.wait_for_visibility_element(page_modal)
        assert page.is_confirmation_modal() is True
        page.confirm_run_task()
        page.wait_for_visibility_element(panel)
        while not page_modal.is_displayed():
            time.sleep(0.2)
        assert (
            page.get_text(page.PAGE_MODAL_TITLE)
            == "Approving association completed successfully"
        )
        page.wait_for_staleness_element(page_modal)


@pytest.mark.dependency(
    name="training_model_logout1", depends=["training_approve_datasets"]
)
def test_training_model_logout_after_approve(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/training/ui"))
    logout(page)


@pytest.mark.dependency(
    name="training_agg_run_login", depends=["training_model_logout1"]
)
def test_training_aggregator_run_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.AGG_OWNER_EMAIL,
        training=True,
    )


@pytest.mark.dependency(name="training_agg_cert", depends=["training_agg_run_login"])
def test_training_aggregator_get_certificate(driver):
    ag = AggregatorsPage(driver)
    ag.open(BASE_URL.format("/aggregators/ui"))
    ag.open_aggregator_by_name(tests_config.TRAINING_AGG_NAME)

    page = AggregatorDetailsPage(driver)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.get_server_certificate()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Server Certificate Retrieved Successfully"
    )
    page.wait_for_staleness_element(page_modal)
    assert "/aggregators/ui/display/1" in page.current_url


@pytest.mark.dependency(name="training_agg_run", depends=["training_agg_cert"])
def test_training_aggregator_run(driver):
    ag = AggregatorsPage(driver)
    ag.open(BASE_URL.format("/aggregators/ui"))
    ag.open_aggregator_by_name(tests_config.TRAINING_AGG_NAME)

    page = AggregatorDetailsPage(driver)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)

    page.run_aggregator_for_experiment(tests_config.TRAINING_EXP_NAME)
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    stop_btn = page.find(page.STOP_BTN)
    while not stop_btn.is_displayed():
        time.sleep(0.2)

    page.click(page.STOP_BTN)
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()

    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert (
        page.get_text(page.PAGE_MODAL_TITLE)
        == "Something went wrong while running the aggregator"
    )


@pytest.mark.dependency(
    name="training_agg_run_logout", depends=["training_agg_run", "lalalala"]
)
def test_training_aggregator_after_run_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/aggregators/ui"))
    logout(page)


@pytest.mark.dependency(
    name="training_data1_train_login", depends=["training_agg_run_logout"]
)
def test_training_data_owner_1_train_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.DSET_OWNER_EMAIL,
        training=True,
    )


@pytest.mark.dependency(
    name="training_data1_start_training", depends=["training_data1_train_login"]
)
def test_training_data_owner_1_start_training(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.TRAINING_DATASET1_NAME)
    page.open(BASE_URL.format("/datasets/ui"))

    old_url = page.current_url
    page.click(page.DATASET_NAME_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.start_training_for_experiment(tests_config.TRAINING_EXP_NAME)

    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    assert "start training for this experiment with this dataset?" in page.get_text(
        page.CONFIRM_TEXT
    )
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    page.wait_for_visibility_element(panel)

    stop_btn = page.find(page.STOP_BTN)
    while not stop_btn.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    page.click(page.STOP_BTN)
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()

    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert page.get_text(page.PAGE_MODAL_TITLE) == "Training Ran Successfully"


@pytest.mark.dependency(
    name="training_data1_train_logout", depends=["training_data1_start_training"]
)
def test_training_data_owner_1_after_train_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/datasets/ui"))
    logout(page)


@pytest.mark.dependency(
    name="training_data2_train_login", depends=["training_data1_train_logout"]
)
def test_training_data_owner_2_train_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.DSET_OWNER2_EMAIL,
        training=True,
    )


@pytest.mark.dependency(
    name="training_data2_start_training", depends=["training_data2_train_login"]
)
def test_training_data_owner_2_start_training(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.TRAINING_DATASET2_NAME)
    page.open(BASE_URL.format("/datasets/ui"))

    old_url = page.current_url
    page.click(page.DATASET_NAME_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.start_training_for_experiment(tests_config.TRAINING_EXP_NAME)

    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    assert "start training for this experiment with this dataset?" in page.get_text(
        page.CONFIRM_TEXT
    )
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not prompt_container.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    page.wait_for_visibility_element(panel)

    stop_btn = page.find(page.STOP_BTN)
    while not stop_btn.is_displayed() and not page_modal.is_displayed():
        time.sleep(0.2)

    page.click(page.STOP_BTN)
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()

    while not page_modal.is_displayed():
        time.sleep(0.2)
    assert page.get_text(page.PAGE_MODAL_TITLE) == "Training Ran Successfully"


@pytest.mark.dependency(
    name="training_data2_train_logout", depends=["training_data2_start_training"]
)
def test_training_data_owner_2_after_train_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/datasets/ui"))
    logout(page)


@pytest.mark.dependency(
    name="training_close_login", depends=["training_data2_train_logout"]
)
def test_training_model_owner_close_event_login(driver):
    page = LoginPage(driver)
    _switch_to_training_mode(driver)
    login(
        page=page,
        url=BASE_URL.format("/benchmarks/ui"),
        email=tests_config.MODEL_OWNER_EMAIL,
        training=True,
    )


@pytest.mark.dependency(name="training_close_event", depends=["training_close_login"])
def test_training_model_owner_close_event(driver):
    listing = TrainingPage(driver)
    listing.open(BASE_URL.format("/training/ui"))
    listing.open_experiment_by_name(tests_config.TRAINING_EXP_NAME)

    ensure_training_event_report_yaml_stub_dict()

    page = TrainingDetailsPage(driver)
    page_modal = page.find(page.PAGE_MODAL)
    panel = page.find(page.PANEL)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    page.close_training_event()
    page.wait_for_visibility_element(page_modal)
    assert page.is_confirmation_modal() is True
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)
    while not page_modal.is_displayed() and not prompt_container.is_displayed():
        time.sleep(0.2)

    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    while not page_modal.is_displayed():
        time.sleep(0.2)

    assert (
        page.get_text(page.PAGE_MODAL_TITLE) == "Closing event completed successfully"
    )
    page.wait_for_staleness_element(page_modal)


@pytest.mark.dependency(name="training_final_logout", depends=["training_close_event"])
def test_training_model_owner_final_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/training/ui"))
    logout(page)
