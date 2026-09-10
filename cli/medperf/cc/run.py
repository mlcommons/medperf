"""One confidential execution: who it is for, where its output goes, and what
identity it runs under.

Everything here is *derived*, never stored. The workload's identity is a
function of facts the server already holds -- the assets by their hashes, the
script by the benchmark, the collector by their key -- which is what lets a
collector who did not run the workload rebuild the very same identity
afterwards and find what was written for them.

That property only holds while there is one derivation. Two would agree until
one of them changed, and the failure is silent: the rebuilt identity names a
storage prefix nothing was ever written to, so the results simply appear not to
exist.
"""

from dataclasses import dataclass

from medperf.cc.collector import CollectorParty
from medperf.cc.config import result_store_for
from medperf.commands.execution.plan import BenchmarkPlan
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.model import Model
from medperf_cc import ResultStore, WorkloadIdentity


@dataclass(frozen=True)
class ConfidentialRun:
    """What both sides of one execution need, worked out the same way."""

    collector: CollectorParty
    result_store: ResultStore
    workload: WorkloadIdentity

    @classmethod
    def resolve(
        cls,
        plan: BenchmarkPlan,
        dataset: Dataset,
        model: Model,
        execution: Execution,
        collector: CollectorParty,
    ) -> "ConfidentialRun":
        """The store and the identity that follow from one collector.

        The collector is passed in rather than worked out here, because how it
        is arrived at differs: an operator resolves it from the asset owners'
        policies before launching, and a collector reads back the one the
        execution was recorded as being for. Everything after that point is
        the same for both.
        """
        return cls(
            collector=collector,
            result_store=result_store_for(collector.settings),
            workload=WorkloadIdentity(
                data_hash=dataset.generated_uid,
                model_hash=model.asset_obj.asset_hash,
                script_hash=plan.script_hash,
                result_collector_hash=collector.key_hash,
                data_id=dataset.id,
                model_id=model.id,
                script_id=plan.script_id,
                execution_id=execution.id,
            ),
        )

    @property
    def store_config(self) -> dict:
        """Where the workload is to write, as it travels to the VM."""
        return self.result_store.store_config(self.workload)

    @property
    def collector_public_key(self) -> str:
        """The key the workload encrypts its results for, as it receives it."""
        return self.collector.public_key.decode("utf-8")
