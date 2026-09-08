"""A model owner running a benchmark: one of their models, many datasets."""

from typing import List, Optional

import medperf.config as config
from medperf.account_management.account_management import get_medperf_user_data
from medperf.commands.association.utils import get_user_associations
from medperf.commands.execution.experiments import Experiment, ExperimentsRunner
from medperf.commands.execution.plan import download_plan_containers, resolve_plan
from medperf.commands.execution.utils import read_uids_file
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.model import Model
from medperf.enums import BenchmarkTopology, Status
from medperf.exceptions import InvalidArgumentError


class ModelBenchmarkRun:
    """Runs one model the caller owns against a benchmark's datasets.

    The mirror of `DatasetBenchmarkRun`, and nobody's to use but the model's
    owner. A model owner never sees the data they run against, so this only
    makes sense for a model that runs inside a confidential VM, against
    datasets that have published one -- and both are checked here rather than
    left to fail once a machine is already running.

    Nothing stands in for the reference model's role on the other side: a data
    owner always has the benchmark's own model to run, but the demo dataset is
    the benchmark's compatibility fixture, not somebody's data, and running
    against it proves nothing about this benchmark's participants.

    Only an `end_to_end_script` benchmark can be run from this side at all.
    Every other topology scores its predictions on-prem, against ground truth
    labels only the data owner holds.
    """

    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        model_uid: int,
        data_uids: Optional[List[int]] = None,
        datasets_input_file: Optional[str] = None,
        ignore_model_errors=False,
        ignore_failed_experiments=False,
        no_cache=False,
        show_summary=False,
        rerun_finalized_executions=False,
    ) -> List[Execution]:
        """Benchmark execution flow, from the model owner's side.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            model_uid (int): UID of the model to run. Must be the caller's own
            data_uids (List|None): list of dataset UIDs to run against.
                                   if None, datasets_input_file will be used
            datasets_input_file: filename to read from
            if data_uids and datasets_input_file are None, use every dataset
            the benchmark approved
        """
        flow = cls(benchmark_uid, model_uid, data_uids, datasets_input_file)
        with flow.ui.interactive():
            flow.prepare()
        flow.validate()
        flow.prepare_datasets()

        return ExperimentsRunner.run(
            benchmark_uid=benchmark_uid,
            plan=flow.plan,
            experiments=flow.experiments(),
            ignore_model_errors=ignore_model_errors,
            ignore_failed_experiments=ignore_failed_experiments,
            no_cache=no_cache,
            rerun_finalized_executions=rerun_finalized_executions,
            show_summary=show_summary,
        )

    def __init__(
        self,
        benchmark_uid: int,
        model_uid: int,
        data_uids: Optional[List[int]] = None,
        datasets_input_file: Optional[str] = None,
    ):
        self.benchmark_uid = benchmark_uid
        self.model_uid = model_uid
        self.data_uids = data_uids
        self.datasets_input_file = datasets_input_file
        self.ui = config.ui
        self.plan = None
        self.datasets = []

    def prepare(self):
        self.benchmark = Benchmark.get(self.benchmark_uid)
        self.ui.print(f"Benchmark Execution: {self.benchmark.name}")
        self.model = Model.get(self.model_uid)
        self.plan = resolve_plan(self.benchmark)
        download_plan_containers(self.plan)

    def validate(self):
        if self.model.owner != get_medperf_user_data()["id"]:
            raise InvalidArgumentError(
                f"Model {self.model_uid} is not yours. Only a model's owner can"
                " run it against a benchmark's datasets; ask the data owner to"
                " run it from their side instead."
            )

        if not self.model.requires_cc():
            raise InvalidArgumentError(
                f"Model {self.model_uid} does not run confidentially, so there"
                " is nothing here for you to operate. The datasets it would run"
                " against are not yours to read, and only their owners can run"
                " it against them."
            )

        if not self.__is_approved_for_benchmark():
            raise InvalidArgumentError(
                f"Model {self.model_uid} is not associated with the specified"
                " benchmark."
            )

        if self.plan.topology is not BenchmarkTopology.END_TO_END_SCRIPT:
            raise InvalidArgumentError(
                f"Benchmark {self.benchmark_uid} scores predictions on-prem,"
                " against ground truth labels only the data owner holds, so"
                " its executions have to be operated by them. Ask the data"
                " owner to run your model from their side."
            )

    def prepare_datasets(self):
        """Which datasets this model will be run against.

        Asking for none means every dataset the benchmark approved, narrowed to
        those configured for confidential computing -- a dataset that has not
        published one has nothing this model could run against. Naming datasets
        explicitly is refused rather than narrowed: a request for something that
        cannot run is a mistake worth hearing about.
        """
        if self.datasets_input_file:
            self.data_uids = read_uids_file(self.datasets_input_file)

        approved = set(Benchmark.get_datasets_uids(self.benchmark_uid))

        if self.data_uids is None:
            self.datasets = self.__configured_for_cc(sorted(approved))
            return

        not_approved = set(self.data_uids).difference(approved)
        if not_approved:
            named = ", ".join(str(uid) for uid in sorted(not_approved))
            subject = (
                f"Datasets of UIDs {named} are"
                if len(not_approved) > 1
                else f"Dataset of UID {named} is"
            )
            raise InvalidArgumentError(
                f"{subject} not associated with the specified benchmark."
            )

        self.datasets = [Dataset.get(data_uid) for data_uid in self.data_uids]
        unconfigured = [
            dataset.id for dataset in self.datasets if not dataset.is_cc_configured()
        ]
        if unconfigured:
            named = ", ".join(str(uid) for uid in unconfigured)
            subject = (
                f"Datasets of UIDs {named} are"
                if len(unconfigured) > 1
                else f"Dataset of UID {named} is"
            )
            raise InvalidArgumentError(
                f"{subject} not configured for confidential computing. That is"
                " for the dataset owner to do before this model can be run"
                " against it."
            )

    def experiments(self) -> List[Experiment]:
        return [
            Experiment(dataset=dataset, model=self.model) for dataset in self.datasets
        ]

    def __is_approved_for_benchmark(self) -> bool:
        """Whether this model may run in this benchmark.

        Read from the caller's own associations rather than from the
        benchmark's model roster: the roster is the whole field of
        competitors, and the server refuses it to a model owner. Their own
        listing answers the question for the models they own, which are the
        only ones this command runs.
        """
        associations = get_user_associations(
            experiment_type="benchmark",
            component_type="model",
            approval_status=Status.APPROVED.value,
        )
        return any(
            association["benchmark"] == self.benchmark_uid
            and association["model"] == self.model_uid
            for association in associations
        )

    def __configured_for_cc(self, data_uids: List[int]) -> List[Dataset]:
        datasets = []
        for data_uid in data_uids:
            dataset = Dataset.get(data_uid)
            if dataset.is_cc_configured():
                datasets.append(dataset)
            else:
                self.ui.print(
                    f"> Skipping dataset {data_uid}: it is not configured for"
                    " confidential computing"
                )
        return datasets
