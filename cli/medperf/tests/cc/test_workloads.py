import pytest

from medperf.cc.workloads import (
    __peer_datasets,
    __peer_models,
    get_approved_component_ids,
    get_associated_benchmarks,
    get_confidential_plan,
)
from medperf.enums import BenchmarkTopology
from medperf.tests.mocks.benchmark import TestBenchmark
from medperf.tests.mocks.cube import TestCube
from medperf_cc import AssetKind, AssetPolicy, Party

PATCH_CC_WORKLOADS = "medperf.cc.workloads.{}"


def a_policy(**overrides) -> AssetPolicy:
    """A valid policy whose collectors these tests do not care about."""
    fields = {"allowed_result_collectors": [Party.DATA_OWNER]}
    fields.update(overrides)
    return AssetPolicy(**fields)


@pytest.mark.parametrize("component_type", ["model", "dataset"])
def test_associated_benchmarks_only_uses_approved_associations(mocker, component_type):
    # Arrange
    spy = mocker.patch(
        PATCH_CC_WORKLOADS.format("get_component_associations"), return_value=[]
    )

    # Act
    get_associated_benchmarks(7, component_type)

    # Assert
    spy.assert_called_once_with(
        component_id=7,
        component_type=component_type,
        experiment_type="benchmark",
        approval_status="APPROVED",
    )


def test_approved_component_ids_only_uses_approved_associations(mocker):
    # Arrange
    spy = mocker.patch(
        PATCH_CC_WORKLOADS.format("get_experiment_associations"),
        return_value=[{"model": 3}, {"model": 5}],
    )

    # Act
    ids = get_approved_component_ids(9, "model")

    # Assert
    spy.assert_called_once_with(
        experiment_id=9,
        experiment_type="benchmark",
        component_type="model",
        approval_status="APPROVED",
    )
    assert ids == [3, 5]


def test_confidential_plan_is_absent_for_container_model_benchmarks():
    # Arrange
    benchmark = TestBenchmark(topology=BenchmarkTopology.BYO_INFERENCE_SCRIPT.value)

    # Act & Assert
    assert get_confidential_plan(benchmark) is None


def test_confidential_plan_is_resolved_for_script_benchmarks(mocker):
    # Arrange
    mocker.patch(
        "medperf.commands.execution.plan.Cube.get", return_value=TestCube(id=7)
    )
    benchmark = TestBenchmark(
        topology=BenchmarkTopology.END_TO_END_SCRIPT.value,
        data_evaluator_mlcube=None,
        benchmark_script=7,
    )

    # Act
    plan = get_confidential_plan(benchmark)

    # Assert
    assert plan.script.id == 7
    assert plan.evaluator is None


def test_a_data_owner_pinning_the_model_skips_models_that_are_not_confidential(mocker):
    # Arrange
    mocker.patch(
        PATCH_CC_WORKLOADS.format("get_approved_component_ids"), return_value=[1, 2]
    )
    confidential = mocker.MagicMock(**{"requires_cc.return_value": True})
    plain = mocker.MagicMock(**{"requires_cc.return_value": False})
    mocker.patch(
        PATCH_CC_WORKLOADS.format("Model.get"),
        side_effect=lambda model_id: confidential if model_id == 1 else plain,
    )

    # Act
    models = __peer_models(TestBenchmark(), a_policy(bind_peer_asset=True))

    # Assert
    assert models == [confidential]


def test_a_sync_that_authorizes_nothing_warns_before_revoking(mocker):
    """Correct when the associations really went away, a silent disaster when a
    peer merely has no certificate yet. The two look identical from here"""
    # Arrange
    from medperf.cc.assets import set_permitted_grants

    ui = mocker.patch("medperf.cc.assets.medperf_config").ui
    asset = mocker.patch("medperf.cc.assets.asset_for")

    # Act
    set_permitted_grants(mocker.MagicMock(), AssetKind.DATA, [])

    # Assert
    ui.print_warning.assert_called_once()
    asset.return_value.set_permitted.assert_called_once_with([])


@pytest.mark.parametrize(
    "kind,peers", [(AssetKind.DATA, __peer_models), (AssetKind.MODEL, __peer_datasets)]
)
def test_peers_are_walked_when_the_collector_is_the_peers_owner(mocker, kind, peers):
    """Not pinning the peer does not mean the peer is irrelevant: releasing
    results to the peer's owner pins *their key*, and there is one per peer"""
    # Arrange
    mocker.patch(
        PATCH_CC_WORKLOADS.format("get_approved_component_ids"), return_value=[1]
    )
    mocker.patch(
        PATCH_CC_WORKLOADS.format("Model.get"),
        return_value=mocker.MagicMock(**{"requires_cc.return_value": True}),
    )
    mocker.patch(
        PATCH_CC_WORKLOADS.format("Dataset.get"), return_value=mocker.MagicMock()
    )
    peer_party = Party.MODEL_OWNER if kind is AssetKind.DATA else Party.DATA_OWNER
    policy = AssetPolicy(bind_peer_asset=False, allowed_result_collectors=[peer_party])

    # Act
    result = peers(TestBenchmark(), policy)

    # Assert
    assert result != [None]
    assert len(result) == 1


@pytest.mark.parametrize("kind", [AssetKind.DATA, AssetKind.MODEL])
def test_a_grant_needing_neither_the_peer_nor_its_owner_covers_every_peer(mocker, kind):
    """Nothing about the grant changes with the peer, so there is nothing to
    enumerate"""
    # Arrange
    spy = mocker.patch(PATCH_CC_WORKLOADS.format("get_approved_component_ids"))
    own_party = Party.DATA_OWNER if kind is AssetKind.DATA else Party.MODEL_OWNER
    policy = AssetPolicy(bind_peer_asset=False, allowed_result_collectors=[own_party])
    peers = __peer_models if kind is AssetKind.DATA else __peer_datasets

    # Act
    result = peers(TestBenchmark(), policy)

    # Assert
    assert result == [None]
    spy.assert_not_called()
