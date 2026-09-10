import pytest

from medperf.commands.execution.confidential_execution import ConfidentialExecution
from medperf.commands.execution.confidential_model_container_execution import (
    ConfidentialModelContainerExecution,
)
from medperf.commands.execution.plan import BenchmarkPlan
from medperf.enums import BenchmarkTopology
from medperf.exceptions import ExecutionError
from medperf.tests.mocks.cube import TestCube
from medperf_cc import Party

PATCH_FLOW = "medperf.commands.execution.confidential_execution.{}"
PATCH_CONTAINER_FLOW = (
    "medperf.commands.execution.confidential_model_container_execution.{}"
)

DATA_OWNER_ID = 20
BENCHMARK_ID = 11
EXECUTION_ID = 42


@pytest.fixture(autouse=True)
def the_operator_collects(mocker):
    """Who the results go to is decided by the asset owners' policies, and is
    covered in `tests/cc/test_collector.py`. These tests are about the flow
    around it, so the operator collects their own."""
    collector = mocker.MagicMock(
        user_id=DATA_OWNER_ID,
        party=Party.DATA_OWNER,
        public_key=b"collector-key",
        settings={"backend": "mock", "root": "/tmp/collect"},
    )
    for module in (PATCH_FLOW, PATCH_CONTAINER_FLOW):
        mocker.patch(module.format("resolve_collector"), return_value=collector)
        mocker.patch(module.format("Benchmark"))
        mocker.patch(module.format("runner_for"))
        mocker.patch(module.format("workload_configs"), return_value=({}, {}))
        mocker.patch(module.format("ConfidentialRun"))
    return collector


class FakeAsset:
    """A dataset or a model, asked only whether it is set up for CC.

    A real object rather than a Mock: an asset is asked `is_cc_configured` and
    a user is asked about one of their roles, so calling the wrong one has to
    fail here rather than quietly return something truthy."""

    def __init__(self, id, owner=None, cc_configured=True):
        self.id = id
        self.owner = owner
        self.cc_configured = cc_configured

    def is_cc_configured(self):
        return self.cc_configured


class FakeRole:
    def __init__(self, configured=True):
        self.configured = configured


class FakeUser:
    """An operator, asked about the roles they hold rather than about "CC"."""

    def __init__(self, id, cc_configured=True):
        self.id = id
        self.cc_operator = FakeRole(cc_configured)
        self.cc_collector = FakeRole(cc_configured)


@pytest.fixture()
def configured(mocker):
    """A dataset, a model and an operator all set up for confidential
    computing."""
    return {
        "dataset": FakeAsset(id=1, owner=DATA_OWNER_ID),
        "model": FakeAsset(id=2),
        "operator": FakeUser(id=DATA_OWNER_ID),
        "execution": mocker.MagicMock(id=EXECUTION_ID),
    }


def plan_for(topology):
    return BenchmarkPlan(
        topology=topology,
        benchmark_id=BENCHMARK_ID,
        script=TestCube(id=7),
        evaluator=TestCube(id=8) if topology.requires_evaluator else None,
    )


@pytest.fixture()
def flow_for(mocker, configured, the_operator_collects):
    """A flow with what `get_operator()` and `prepare()` would have resolved
    already in place, so each test can start at the step it is about."""

    def _flow(cls, topology):
        flow = cls(
            plan_for(topology),
            configured["dataset"],
            configured["model"],
            configured["execution"],
        )
        flow.operator = configured["operator"]
        flow.confidential_run = mocker.MagicMock(collector=the_operator_collects)
        return flow

    return _flow


def test_predictions_scored_on_prem_need_the_data_owner(configured, flow_for):
    """An inference_script benchmark scores its predictions against ground
    truth labels nobody but the data owner holds"""
    # Arrange
    configured["operator"] = FakeUser(id=99)
    flow = flow_for(
        ConfidentialModelContainerExecution, BenchmarkTopology.INFERENCE_SCRIPT
    )

    # Act & Assert
    with pytest.raises(ExecutionError, match="operated by the data owner"):
        flow.validate()


def test_the_data_owner_may_operate_their_own_inference_run(configured, flow_for):
    # Arrange
    flow = flow_for(
        ConfidentialModelContainerExecution, BenchmarkTopology.INFERENCE_SCRIPT
    )

    # Act & Assert
    flow.validate()


def test_an_end_to_end_run_may_be_operated_by_anyone(configured, flow_for):
    """The metric is computed inside the VM, so no on-prem labels are involved
    and there is nothing tying the run to the data owner"""
    # Arrange
    configured["operator"] = FakeUser(id=99)
    flow = flow_for(ConfidentialExecution, BenchmarkTopology.END_TO_END_SCRIPT)

    # Act & Assert
    flow.validate()


@pytest.mark.parametrize("unconfigured", ["dataset", "model", "operator"])
def test_every_party_must_be_configured_for_confidential_computing(
    configured, unconfigured, flow_for
):
    # Arrange
    party = configured[unconfigured]
    if isinstance(party, FakeUser):
        party.cc_operator = FakeRole(configured=False)
    else:
        party.cc_configured = False
    flow = flow_for(ConfidentialExecution, BenchmarkTopology.END_TO_END_SCRIPT)

    # Act & Assert
    with pytest.raises(ExecutionError):
        flow.validate()


def test_results_are_not_downloaded_before_they_are_there(mocker, flow_for):
    """A runner starts a workload and returns; fetching straight away would
    pick up whatever happens to be there, which is nothing"""
    # Arrange
    flow = flow_for(ConfidentialExecution, BenchmarkTopology.END_TO_END_SCRIPT)
    order = []
    mocker.patch(
        PATCH_FLOW.format("results_exist"),
        side_effect=lambda *a: order.append("check") or True,
    )
    mocker.patch(
        PATCH_FLOW.format("download_metrics"),
        side_effect=lambda *a: order.append("download") or ({}, None),
    )

    # Act
    flow.collect_results()

    # Assert
    assert order == ["check", "download"]


def test_a_workload_that_produced_nothing_is_reported(mocker, flow_for):
    # Arrange
    flow = flow_for(ConfidentialExecution, BenchmarkTopology.END_TO_END_SCRIPT)
    mocker.patch(PATCH_FLOW.format("results_exist"), return_value=False)

    # Act & Assert
    with pytest.raises(ExecutionError, match="did not complete"):
        flow.collect_results()


def test_an_operator_who_is_not_the_collector_downloads_nothing(
    mocker, the_operator_collects, flow_for
):
    """The results are encrypted for somebody else's key and written to
    somebody else's storage. Trying would fail; pretending would report an
    execution that produced nothing"""
    # Arrange
    the_operator_collects.user_id = 12345
    flow = flow_for(ConfidentialExecution, BenchmarkTopology.END_TO_END_SCRIPT)
    download = mocker.patch(PATCH_FLOW.format("download_metrics"))
    ready = mocker.patch(PATCH_FLOW.format("results_exist"))

    # Act
    flow.collect_results()

    # Assert
    download.assert_not_called()
    ready.assert_not_called()
    assert flow.results == {}
