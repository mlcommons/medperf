"""Turning benchmark associations into the grants an asset owner publishes.

A confidential computing policy answers one question: which workloads may
decrypt this asset? Both sides build that answer out of benchmark associations,
and what each of them has to enumerate follows from the terms its owner pins:
an owner who does not pin the peer asset writes the same grant for every
peer, so there is nothing to enumerate.
"""

from typing import List, Optional

from medperf.cc.config import policy_of
from medperf.cc.parties import (
    collector_key_hashes,
    party_owners,
    peer_key_hashes,
)
from medperf.commands.association.utils import (
    get_component_associations,
    get_experiment_associations,
)
from medperf.commands.execution.plan import BenchmarkPlan, resolve_plan
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.model import Model
from medperf.enums import Status
from medperf_cc import AssetKind, WorkloadGrant
from medperf_cc import AssetPolicy


def get_associated_benchmarks(
    component_id: int, component_type: str
) -> List[Benchmark]:
    """The benchmarks a dataset or a model is *approved* to take part in.

    Only approved, current associations are considered. A pending request has
    not been granted yet and a rejected or superseded one has been taken away,
    and neither should hand out decryption rights."""
    assocs = get_component_associations(
        component_id=component_id,
        component_type=component_type,
        experiment_type="benchmark",
        approval_status=Status.APPROVED.value,
    )
    return [Benchmark.get(assoc["benchmark"]) for assoc in assocs]


def get_approved_component_ids(benchmark_id: int, component_type: str) -> List[int]:
    """The datasets or models *approved* to take part in a benchmark."""
    assocs = get_experiment_associations(
        experiment_id=benchmark_id,
        experiment_type="benchmark",
        component_type=component_type,
        approval_status=Status.APPROVED.value,
    )
    return [assoc[component_type] for assoc in assocs]


def get_confidential_plan(benchmark: Benchmark) -> BenchmarkPlan:
    """The resolved plan of a benchmark that can host confidential workloads.

    Returns None for benchmarks whose topology has no benchmark script: those
    run container models, which are never loaded into a confidential VM."""
    if not benchmark.topology_enum.requires_benchmark_script:
        return None
    return resolve_plan(benchmark)


def get_dataset_grants(dataset: Dataset) -> List[WorkloadGrant]:
    """What a data owner authorizes to read their data.

    One grant per combination they pin. A peer they did not pin is left out of
    the grant, which then covers every peer -- but the peers are still walked
    when the collector is the peer's owner, because each of those has a key of
    their own."""
    policy = policy_of(dataset)
    collectors = policy.allowed_result_collectors

    grants = []
    for benchmark in get_associated_benchmarks(dataset.id, "dataset"):
        plan = get_confidential_plan(benchmark)
        if plan is None:
            continue
        peer_hashes = peer_key_hashes(benchmark.id, AssetKind.MODEL)
        for model in __peer_models(benchmark, policy):
            owners = party_owners(benchmark, dataset=dataset, model=model)
            for collector_hash in collector_key_hashes(collectors, owners, peer_hashes):
                grants.append(
                    WorkloadGrant(
                        data_hash=dataset.generated_uid,
                        model_hash=(
                            model.asset_obj.asset_hash
                            if policy.bind_peer_asset
                            else None
                        ),
                        script_hash=plan.script_hash,
                        result_collector_hash=collector_hash,
                    )
                )
    return grants


def get_model_grants(model: Model) -> List[WorkloadGrant]:
    """What a model owner authorizes to load their weights."""
    policy = policy_of(model)
    collectors = policy.allowed_result_collectors
    asset_hash = model.asset_obj.asset_hash

    grants = []
    for benchmark in get_associated_benchmarks(model.id, "model"):
        plan = get_confidential_plan(benchmark)
        if plan is None:
            continue
        peer_hashes = peer_key_hashes(benchmark.id, AssetKind.DATA)
        for dataset in __peer_datasets(benchmark, policy):
            owners = party_owners(benchmark, dataset=dataset, model=model)
            for collector_hash in collector_key_hashes(collectors, owners, peer_hashes):
                grants.append(
                    WorkloadGrant(
                        data_hash=(
                            dataset.generated_uid if policy.bind_peer_asset else None
                        ),
                        model_hash=asset_hash,
                        script_hash=plan.script_hash,
                        result_collector_hash=collector_hash,
                    )
                )
    return grants


def __peer_models(benchmark: Benchmark, policy: AssetPolicy) -> List[Optional[Model]]:
    """The models a data owner's grant has to be written out for, one each.

    Only confidential models: the rest never enter a VM, so no grant of theirs
    could be used."""
    if not policy.needs_peer(AssetKind.DATA):
        return [None]

    models = [
        Model.get(model_id)
        for model_id in get_approved_component_ids(benchmark.id, "model")
    ]
    return [model for model in models if model.requires_cc()]


def __peer_datasets(
    benchmark: Benchmark, policy: AssetPolicy
) -> List[Optional[Dataset]]:
    """The datasets a model owner's grant has to be written out for, one each."""
    if not policy.needs_peer(AssetKind.MODEL):
        return [None]

    return [
        Dataset.get(dataset_id)
        for dataset_id in get_approved_component_ids(benchmark.id, "dataset")
    ]
