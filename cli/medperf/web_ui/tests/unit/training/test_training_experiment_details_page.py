import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

from medperf.tests.mocks.cube import TestCube
import pytest
from selenium.common.exceptions import NoSuchElementException

from medperf.tests.mocks.training_exp import TestTrainingExp
from medperf.web_ui.tests import config as tests_config
from medperf.web_ui.tests.pages.training.details_page import TrainingDetailsPage
from medperf.web_ui.tests.unit.helpers import switch_to_ui_mode

BASE_URL = tests_config.BASE_URL

PREP_CUBE = TestCube(id=1, name="prep")
FL_CUBE = TestCube(id=2, name="fl")
TEST_CONTAINERS = [PREP_CUBE, FL_CUBE]
TEST_AGG = SimpleNamespace(id=5, name="agg", address="127.0.0.1", port=7000, owner=1)


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
