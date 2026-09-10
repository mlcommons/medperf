"""Picking up the results of a confidential execution somebody else ran.

Downloading and opening only. What comes out is written where every other
execution writes its results, so reporting them is `medperf result submit`,
the same command as for anything else.
"""

from medperf import config
from medperf.account_management import get_medperf_user_object
from medperf.cc.collector import resolve_collector
from medperf.cc.errors import as_medperf_error
from medperf.cc.results import download_metrics, results_exist
from medperf.cc.run import ConfidentialRun
from medperf.commands.execution.plan import resolve_plan
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.model import Model
from medperf.exceptions import ExecutionError


class DownloadCCResults:
    """Fetches and opens one confidential execution's results.

    The other half of a run whose operator is not its collector. The operator
    started the workload and stopped there -- the results were written to this
    user's storage, encrypted for this user's key, and nobody else can do this
    part.

    Also usable when the operator was the collector and the inline collection
    did not happen or has to be repeated: it reads the same execution and
    rebuilds the same workload identity, so it lands in the same place.

    Reporting them is a separate step, and the ordinary one.
    """

    @classmethod
    @as_medperf_error()
    def run(cls, execution_uid: int):
        flow = cls(execution_uid)
        flow.load()
        flow.validate()
        with config.ui.interactive():
            flow.collect()
        flow.write()
        return flow.results

    def __init__(self, execution_uid: int):
        self.execution_uid = execution_uid
        self.results = {}
        self.integrity_proof = None

    def load(self):
        self.user = get_medperf_user_object()
        self.execution = Execution.get(self.execution_uid)
        self.benchmark = Benchmark.get(self.execution.benchmark)
        self.dataset = Dataset.get(self.execution.dataset)
        self.model = Model.get(self.execution.model)
        self.plan = resolve_plan(self.benchmark)
        # Who these results were sealed for: the asset owners' policies said
        # so before the execution existed, and they are the only thing that
        # says it. What the server recorded grants this user permission to
        # read and report the execution; it decides nothing here.
        self.collector = resolve_collector(
            self.benchmark, self.dataset, self.model
        )

    def validate(self):
        if self.collector.user_id != self.user.id:
            raise ExecutionError(
                f"These results were written for the {self.collector.party.value},"
                " who is not you. They are encrypted for their key, so only they"
                " can open them."
            )
        if not self.user.cc_collector.configured:
            raise ExecutionError(
                "You have not configured anywhere to receive results."
                " Run `medperf confidential setup_cc_collector` first."
            )

    def collect(self):
        # Resolved after validate(), so that "these are not yours" is what a
        # user hears rather than something about somebody else's storage.
        run = ConfidentialRun.resolve(
            self.plan, self.dataset, self.model, self.execution, self.collector
        )
        if not results_exist(run.result_store, run.workload):
            raise ExecutionError(
                f"Execution {self.execution_uid} has left no results to collect."
                " The workload may still be running, or may have failed."
            )
        self.results, self.integrity_proof = download_metrics(
            run.result_store, run.workload, self.execution.id
        )

    def write(self):
        """Puts the results where an execution's results live.

        The same place the inline path writes them, so what happens next is the
        same too: `medperf result submit` reports them, and nothing about this
        execution being collected by a second party makes it a special case."""
        self.execution.save_results(
            self.results,
            partial=False,
            integrity_proof=(
                self.integrity_proof.todict() if self.integrity_proof else {}
            ),
        )
        self.execution.mark_as_executed()
        self.execution.write()
        config.ui.print(
            "Results collected. Report them with"
            f" `medperf result submit -r {self.execution.id}`."
        )
