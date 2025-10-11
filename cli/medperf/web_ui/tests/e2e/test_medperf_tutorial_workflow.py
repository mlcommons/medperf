import pytest
import time

from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.base_page import BasePage
from medperf.web_ui.tests.pages.security_page import SecurityPage
from medperf.web_ui.tests.pages.settings_page import SettingsPage
from medperf.web_ui.tests.pages.login_page import LoginPage

from medperf.web_ui.tests.pages.benchmark.workflow_test_page import WorkflowTestPage
from medperf.web_ui.tests.pages.benchmark.register_page import RegBenchmarkPage
from medperf.web_ui.tests.pages.benchmark.details_page import BenchmarkDetailsPage

from medperf.web_ui.tests.pages.container.compatibility_test_page import (
    CompatibilityTestPage,
)
from medperf.web_ui.tests.pages.container.register_page import RegContainerPage
from medperf.web_ui.tests.pages.container.details_page import ContainerDetailsPage

from medperf.web_ui.tests.pages.dataset.register_page import RegDatasetPage
from medperf.web_ui.tests.pages.dataset.details_page import DatasetDetailsPage

from medperf.web_ui.tests.e2e.functions.common import login, logout

BASE_URL = tests_config.BASE_URL


@pytest.mark.dependency(name="security_test_token")
def test_security_page_token(driver, sec_token):
    page = SecurityPage(driver)
    page.open(BASE_URL.format("/"))

    assert "/security_check" in page.current_url

    old_url = page.current_url
    page.enter_token(token=sec_token)
    page.wait_for_url_change(old_url)

    assert "/security_check" not in page.current_url

    page.driver.delete_all_cookies()


@pytest.mark.dependency(name="security_test_url", depends=["security_test_token"])
def test_security_page_url(driver, sec_token):
    page = BasePage(driver)
    page.open(BASE_URL.format("/security_check") + f"?token={sec_token}")

    assert "/security_check" not in page.current_url


@pytest.mark.dependency(name="activate_profile", depends=["security_test_url"])
def test_activate_local_profiile(driver):
    page = SettingsPage(driver)
    page.open(BASE_URL.format("/profiles"))

    current_profile = page.get_text(page.CURRENT_PROFILE)
    if current_profile == tests_config.LOCAL_PROFILE:
        return

    assert page.find(page.ACTIVATE).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False

    page.activate_profile(profile_name=tests_config.LOCAL_PROFILE)

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Profile Activated Successfully"

    page.wait_for_staleness_element(popup_modal)

    assert page.get_text(page.CURRENT_PROFILE) == tests_config.LOCAL_PROFILE


@pytest.mark.dependency(name="logout_if_logged_in", depends=["activate_profile"])
def test_logout_if_logged_in(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    if "/medperf_login?redirected=true" not in page.current_url:
        logout(page)


@pytest.mark.dependency(name="benchmark_login", depends=["logout_if_logged_in"])
def test_benchmark_login(driver):
    page = LoginPage(driver)
    url = BASE_URL.format("/benchmarks/ui")

    login(page=page, url=url, email=tests_config.BMK_OWNER_EMAIL)


@pytest.mark.dependency(name="workflow_test", depends=["benchmark_login"])
def test_benchmark_workflow_test(driver):
    page = WorkflowTestPage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    old_url = page.current_url
    page.click(page.BMK_REG_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/benchmarks/register/ui" in page.current_url

    old_url = page.current_url
    page.click(page.WF_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/benchmarks/register/workflow_test" in page.current_url
    assert page.find(page.RUN_TEST_BTN).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    next_modal = page.find(page.NEXT_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert next_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.run_test(
        data_prep_path=tests_config.DATA_PREP_PATH,
        model_path=tests_config.MODEL_PATH,
        evaluator_path=tests_config.EVALUATOR_PATH,
        data_path=tests_config.DATA_PATH,
        labels_path=tests_config.LABELS_PATH,
    )

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not next_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert next_modal.is_displayed() is True
    assert page.get_text(page.NEXT_TITLE) == "Benchmark Workflow Test Successful"

    continue_btn = next_modal.find_element(*page.CONTINUE_BTN)
    page.ensure_element_ready(continue_btn)
    continue_btn.click()
    page.wait_for_staleness_element(next_modal)
    page.wait_for_url_change(old_url)

    assert "/benchmarks/register/ui" in page.current_url


@pytest.mark.dependency(name="register_data_prep", depends=["workflow_test"])
def test_benchmark_register_data_prep_container(driver):
    page = RegContainerPage(driver)
    page.open(BASE_URL.format("/containers/ui"))

    old_url = page.current_url
    page.click(page.REG_CONTAINER_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/containers/register/ui" in page.current_url
    assert page.find(page.REGISTER).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.register_container(container_dict=tests_config.DATA_PREPARATOR_CONTAINER)

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Model Registered Successfully"

    page.wait_for_staleness_element(popup_modal)
    page.wait_for_url_change(old_url)

    assert "/containers/ui/display/" in page.current_url


@pytest.mark.dependency(name="register_ref_model", depends=["register_data_prep"])
def test_benchmark_register_reference_model_container(driver):
    page = RegContainerPage(driver)
    page.open(BASE_URL.format("/containers/ui"))

    old_url = page.current_url
    page.click(page.REG_CONTAINER_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/containers/register/ui" in page.current_url
    assert page.find(page.REGISTER).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.register_container(container_dict=tests_config.REF_MODEL_CONTAINER)

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Model Registered Successfully"

    page.wait_for_staleness_element(popup_modal)
    page.wait_for_url_change(old_url)

    assert "/containers/ui/display/" in page.current_url


@pytest.mark.dependency(name="register_metrics", depends=["register_ref_model"])
def test_benchmark_register_metrics_container(driver):
    page = RegContainerPage(driver)
    page.open(BASE_URL.format("/containers/ui"))

    old_url = page.current_url
    page.click(page.REG_CONTAINER_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/containers/register/ui" in page.current_url
    assert page.find(page.REGISTER).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.register_container(container_dict=tests_config.METRICS_CONTAINER)

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Model Registered Successfully"

    page.wait_for_staleness_element(popup_modal)
    page.wait_for_url_change(old_url)

    assert "/containers/ui/display/" in page.current_url


@pytest.mark.dependency(name="register_benchmark", depends=["register_metrics"])
def test_benchmark_registration(driver):
    page = RegBenchmarkPage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    old_url = page.current_url
    page.click(page.REG_BMK_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/benchmarks/register/ui" in page.current_url
    assert page.find(page.REGISTER).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.register_benchmark(
        name=tests_config.BMK_NAME,
        description=tests_config.BMK_DESC,
        reference_dataset=tests_config.REF_DATASET_TARBALL,
        data_preparator=tests_config.DATA_PREP_NAME,
        reference_model=tests_config.REF_MODEL_NAME,
        metrics=tests_config.METRICS_NAME,
    )

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Benchmark Successfully Registered"

    page.wait_for_staleness_element(popup_modal)
    page.wait_for_url_change(old_url)

    assert "/benchmarks/ui/display/" in page.current_url


@pytest.mark.dependency(name="benchmark_logout", depends=["register_benchmark"])
def test_benchmark_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    logout(page)


@pytest.mark.dependency(name="model_login", depends=["benchmark_logout"])
def test_model_login(driver):
    page = LoginPage(driver)
    url = BASE_URL.format("/containers/ui")

    login(page=page, url=url, email=tests_config.MODEL_OWNER_EMAIL)


@pytest.mark.dependency(name="comp_test", depends=["model_login"])
def test_container_comp_test(driver):
    page = CompatibilityTestPage(driver)
    page.open(BASE_URL.format("/containers/ui"))

    old_url = page.current_url
    page.click(page.REG_CONT_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/containers/register/ui" in page.current_url

    old_url = page.current_url
    page.click(page.COMP_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/containers/register/compatibility_test" in page.current_url
    assert page.find(page.RUN_TEST_BTN).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    next_modal = page.find(page.NEXT_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert next_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.run_test(
        benchmark=tests_config.BMK_NAME, container_path=tests_config.CONTAINER_PATH
    )

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not next_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert next_modal.is_displayed() is True
    assert page.get_text(page.NEXT_TITLE) == "Model Compatibility Test Successful"

    continue_btn = next_modal.find_element(*page.CONTINUE_BTN)
    page.ensure_element_ready(continue_btn)
    continue_btn.click()
    page.wait_for_staleness_element(next_modal)
    page.wait_for_url_change(old_url)

    assert "/containers/register/ui" in page.current_url


@pytest.mark.dependency(name="container_registration", depends=["comp_test"])
def test_container_registration(driver):
    page = RegContainerPage(driver)
    page.open(BASE_URL.format("/containers/ui"))

    old_url = page.current_url
    page.click(page.REG_CONTAINER_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/containers/register/ui" in page.current_url
    assert page.find(page.REGISTER).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.register_container(container_dict=tests_config.CONTAINER)

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Model Registered Successfully"

    page.wait_for_staleness_element(popup_modal)
    page.wait_for_url_change(old_url)

    assert "/containers/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="container_association", depends=["container_registration"]
)
def test_container_association(driver):
    page = ContainerDetailsPage(
        driver,
        container=tests_config.CONTAINER["name"],
        benchmark=tests_config.BMK_NAME,
    )
    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)
    text_container = page.find(page.TEXT_CONTAINER)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False
    assert text_container.is_displayed() is False
    assert prompt_container.is_displayed() is False

    page.request_association()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while (
        not prompt_container.is_displayed()
        and not popup_modal.is_displayed()
        and not error_modal.is_displayed()
    ):
        time.sleep(0.2)

    assert text_container.is_displayed() is True
    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Association Requested Successfully"

    page.wait_for_staleness_element(popup_modal)

    assert "/containers/ui/display/" in page.current_url
    assert tests_config.BMK_NAME in page.get_association_cards_titles()


@pytest.mark.dependency(name="model_logout", depends=["container_association"])
def test_model_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    logout(page)


@pytest.mark.dependency(name="dataset_login", depends=["model_logout"])
def test_dataset_login(driver):
    page = LoginPage(driver)
    url = BASE_URL.format("/datasets/ui")

    login(page=page, url=url, email=tests_config.DSET_OWNER_EMAIL)


@pytest.mark.dependency(name="dataset_registration", depends=["dataset_login"])
def test_dataset_registration(driver):
    page = RegDatasetPage(driver)
    page.open(BASE_URL.format("/datasets/ui"))

    old_url = page.current_url
    page.click(page.REG_DSET_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/datasets/register/ui" in page.current_url
    assert page.find(page.REGISTER).is_enabled() is False

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    text_container = page.find(page.TEXT_CONTAINER)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert text_container.is_displayed() is False
    assert prompt_container.is_displayed() is False

    page.register_dataset(
        benchmark=tests_config.BMK_NAME,
        name=tests_config.DATASET_NAME,
        description=tests_config.DATASET_DESC,
        location=tests_config.DATASET_LOCATION,
        data_path=tests_config.DATASET_DATA_PATH,
        labels_path=tests_config.DATASET_LABELS_PATH,
    )

    old_url = page.current_url
    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    while (
        not prompt_container.is_displayed()
        and not popup_modal.is_displayed()
        and not error_modal.is_displayed()
    ):
        time.sleep(0.2)

    assert text_container.is_displayed() is True
    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Dataset Registered Successfully"

    page.wait_for_staleness_element(popup_modal)
    page.wait_for_url_change(old_url)

    assert "/datasets/ui/display/" in page.current_url


@pytest.mark.dependency(name="dataset_preparation", depends=["dataset_registration"])
def test_dataset_preparation(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.DATASET_NAME)

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.prepare_dataset()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Dataset Prepared Successfully"

    page.wait_for_staleness_element(popup_modal)

    assert "/datasets/ui/display/" in page.current_url

    page.wait_for_presence_selector(page.PREPARED_TEXT)


@pytest.mark.dependency(name="dataset_set_operational", depends=["dataset_preparation"])
def test_dataset_set_operational(driver):
    page = DatasetDetailsPage(driver, dataset=tests_config.DATASET_NAME)

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    text_container = page.find(page.TEXT_CONTAINER)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert text_container.is_displayed() is False
    assert prompt_container.is_displayed() is False

    page.set_operational()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    while (
        not prompt_container.is_displayed()
        and not popup_modal.is_displayed()
        and not error_modal.is_displayed()
    ):
        time.sleep(0.2)

    assert text_container.is_displayed() is True
    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Dataset Set to Operation Successfully"

    page.wait_for_staleness_element(popup_modal)

    assert "/datasets/ui/display/" in page.current_url

    page.wait_for_presence_selector(page.SET_OPERATIONAL_TEXT)


@pytest.mark.dependency(name="dataset_association", depends=["dataset_set_operational"])
def test_dataset_association(driver):
    page = DatasetDetailsPage(
        driver, dataset=tests_config.DATASET_NAME, benchmark=tests_config.BMK_NAME
    )

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)
    text_container = page.find(page.TEXT_CONTAINER)
    prompt_container = page.find(page.PROMPT_CONTAINER)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False
    assert text_container.is_displayed() is False
    assert prompt_container.is_displayed() is False

    page.request_association()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while (
        not prompt_container.is_displayed()
        and not popup_modal.is_displayed()
        and not error_modal.is_displayed()
    ):
        time.sleep(0.2)

    assert text_container.is_displayed() is True
    assert prompt_container.is_displayed() is True

    page.click(page.RESPOND_YES)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Association Requested Successfully"

    page.wait_for_staleness_element(popup_modal)

    assert "/datasets/ui/display/" in page.current_url
    assert tests_config.BMK_NAME in page.get_association_cards_titles()


@pytest.mark.dependency(name="dataset_logout", depends=["dataset_association"])
def test_dataset_logout(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    logout(page)


@pytest.mark.dependency(name="benchmark_login1", depends=["dataset_logout"])
def test_benchmark_login1(driver):
    page = LoginPage(driver)
    url = BASE_URL.format("/benchmarks/ui")

    login(page=page, url=url, email=tests_config.BMK_OWNER_EMAIL)


@pytest.mark.dependency(name="benchmark_approve_dataset", depends=["benchmark_login1"])
def test_benchmark_approve_dataset(driver):
    page = BenchmarkDetailsPage(
        driver, benchmark=tests_config.BMK_NAME, entity_name=tests_config.DATASET_NAME
    )
    page.open(BASE_URL.format("/benchmarks/ui"))

    old_url = page.current_url
    page.click(page.BMK_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/benchmarks/ui/display/" in page.current_url

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False

    page.approve_dataset()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Association Approved Successfully"

    page.wait_for_staleness_element(popup_modal)

    assert "/benchmarks/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="benchmark_approve_container", depends=["benchmark_approve_dataset"]
)
def test_benchmark_approve_container(driver):
    page = BenchmarkDetailsPage(
        driver,
        benchmark=tests_config.BMK_NAME,
        entity_name=tests_config.CONTAINER["name"],
    )

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False

    page.approve_container()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Association Approved Successfully"

    page.wait_for_staleness_element(popup_modal)

    assert "/benchmarks/ui/display/" in page.current_url


@pytest.mark.dependency(
    name="benchmark_logout1", depends=["benchmark_approve_container"]
)
def test_benchmark_logout1(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    logout(page)


@pytest.mark.dependency(name="dataset_login1", depends=["benchmark_logout1"])
def test_dataset_login1(driver):
    page = LoginPage(driver)
    url = BASE_URL.format("/datasets/ui")

    login(page=page, url=url, email=tests_config.DSET_OWNER_EMAIL)


@pytest.mark.dependency(name="dataset_run_execution", depends=["dataset_login1"])
def test_dataset_run_execution(driver):
    page = DatasetDetailsPage(
        driver, dataset=tests_config.DATASET_NAME, benchmark=tests_config.BMK_NAME
    )
    page.open(BASE_URL.format("/datasets/ui"))

    old_url = page.current_url
    page.click(page.DATASET_NAME_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/datasets/ui/display/" in page.current_url

    confirm_modal = page.find(page.CONFIRM_MODAL)
    popup_modal = page.find(page.POPUP_MODAL)
    error_modal = page.find(page.ERROR_MODAL)
    panel = page.find(page.PANEL)

    assert confirm_modal.is_displayed() is False
    assert popup_modal.is_displayed() is False
    assert error_modal.is_displayed() is False
    assert panel.is_displayed() is False

    page.run_execution()

    page.wait_for_visibility_element(confirm_modal)
    page.confirm_run_task()
    page.wait_for_visibility_element(panel)

    while not popup_modal.is_displayed() and not error_modal.is_displayed():
        time.sleep(0.2)

    assert popup_modal.is_displayed() is True
    assert page.get_text(page.POPUP_TITLE) == "Execution Ran Successfully"

    page.wait_for_staleness_element(popup_modal)

    assert "/datasets/ui/display/" in page.current_url


@pytest.mark.dependency(name="dataset_view_results", depends=["dataset_run_execution"])
def test_dataset_view_results(driver):
    page = DatasetDetailsPage(
        driver, dataset=tests_config.DATASET_NAME, benchmark=tests_config.BMK_NAME
    )

    page.view_results()


@pytest.mark.dependency(name="dataset_submit_results", depends=["dataset_view_results"])
def test_dataset_submit_results(driver):
    page = DatasetDetailsPage(
        driver, dataset=tests_config.DATASET_NAME, benchmark=tests_config.BMK_NAME
    )

    submit_btns = page.get_submit_buttons()
    for _ in range(len(submit_btns)):
        submit_btns = page.get_submit_buttons()
        confirm_modal = page.find(page.CONFIRM_MODAL)
        popup_modal = page.find(page.POPUP_MODAL)
        error_modal = page.find(page.ERROR_MODAL)
        text_container = page.find(page.TEXT_CONTAINER)
        prompt_container = page.find(page.PROMPT_CONTAINER)

        assert confirm_modal.is_displayed() is False
        assert popup_modal.is_displayed() is False
        assert error_modal.is_displayed() is False
        assert text_container.is_displayed() is False
        assert prompt_container.is_displayed() is False

        page.submit_result(submit_btns[0])

        page.wait_for_visibility_element(confirm_modal)
        page.confirm_run_task()

        while (
            not prompt_container.is_displayed()
            and not popup_modal.is_displayed()
            and not error_modal.is_displayed()
        ):
            time.sleep(0.2)

        assert text_container.is_displayed() is True
        assert prompt_container.is_displayed() is True

        page.click(page.RESPOND_YES)

        while not popup_modal.is_displayed() and not error_modal.is_displayed():
            time.sleep(0.2)

        assert popup_modal.is_displayed() is True
        assert page.get_text(page.POPUP_TITLE) == "Results Successfully Submitted"

        page.wait_for_staleness_element(popup_modal)

        assert "/datasets/ui/display/" in page.current_url


@pytest.mark.dependency(name="dataset_logout1", depends=["dataset_submit_results"])
def test_dataset_logout1(driver):
    page = BasePage(driver)
    page.open(BASE_URL.format("/benchmarks/ui"))

    logout(page)


@pytest.mark.dependency(name="benchmark_login2", depends=["dataset_logout1"])
def test_benchmark_login2(driver):
    page = LoginPage(driver)
    url = BASE_URL.format("/benchmarks/ui")

    login(page=page, url=url, email=tests_config.BMK_OWNER_EMAIL)


@pytest.mark.dependency(name="benchmark_View_results", depends=["benchmark_login2"])
def test_benchmark_view_results(driver):
    page = BenchmarkDetailsPage(driver, benchmark=tests_config.BMK_NAME)
    page.open(BASE_URL.format("/benchmarks/ui"))

    old_url = page.current_url
    page.click(page.BMK_BTN)
    page.wait_for_url_change(old_url)
    page.wait_for_presence_selector(page.NAVBAR)

    assert "/benchmarks/ui/display/" in page.current_url

    page.view_results()
