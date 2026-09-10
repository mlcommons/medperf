"""A data owner running a benchmark: one of their datasets, many models."""

from typing import List, Optional

import medperf.config as config
from medperf.commands.execution.experiments import Experiment, ExperimentsRunner
from medperf.commands.execution.plan import download_plan_containers, resolve_plan
from medperf.commands.execution.utils import read_uids_file
from medperf.entities.benchmark import Benchmark
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.model import Model
from medperf.exceptions import InvalidArgumentError


class DatasetBenchmarkRun:
    """Runs a benchmark's models against one dataset the caller owns.

    The data owner's side of a benchmark, and the only side that reads the
    benchmark's model roster: that listing is what tells a data owner what
    there is to run, and the server lets them read it. A model owner is
    refused it -- it would show them their competitors -- and runs their own
    model through `ModelBenchmarkRun` instead.
    """

    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        data_uid: int,
        models_uids: Optional[List[int]] = None,
        models_input_file: Optional[str] = None,
        ignore_model_errors=False,
        ignore_failed_experiments=False,
        no_cache=False,
        show_summary=False,
        rerun_finalized_executions=False,
    ) -> List[Execution]:
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (int): Registered Dataset UID
            models_uids (List|None): list of model UIDs to execute.
                                    if None, models_input_file will be used
            models_input_file: filename to read from
            if models_uids and models_input_file are None, use all benchmark models
        """
        flow = cls(benchmark_uid, data_uid, models_uids, models_input_file)
        with flow.ui.interactive():
            flow.prepare()
        flow.validate()
        flow.prepare_models()

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
        data_uid: int,
        models_uids: Optional[List[int]] = None,
        models_input_file: Optional[str] = None,
    ):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.models_uids = models_uids
        self.models_input_file = models_input_file
        self.ui = config.ui
        self.plan = None

    def prepare(self):
        self.benchmark = Benchmark.get(self.benchmark_uid)
        self.ui.print(f"Benchmark Execution: {self.benchmark.name}")
        self.dataset = Dataset.get(self.data_uid)
        self.plan = resolve_plan(self.benchmark)
        download_plan_containers(self.plan)

    def validate(self):
        dset_prep_cube = self.dataset.data_preparation_mlcube
        bmark_prep_cube = self.benchmark.data_preparation_mlcube

        if self.dataset.id is None:
            msg = "The provided dataset is not registered."
            raise InvalidArgumentError(msg)

        if self.dataset.state != "OPERATION":
            msg = "The provided dataset is not operational."
            raise InvalidArgumentError(msg)

        if dset_prep_cube != bmark_prep_cube:
            msg = "The provided dataset is not compatible with the specified benchmark."
            raise InvalidArgumentError(msg)
        # TODO: there is no check if dataset is associated with the benchmark
        #       Note that if it is present, this will break dataset association creation logic

    def prepare_models(self):
        """Which models this dataset will be run against.

        Asking for none means every model the benchmark approved, plus its
        reference model -- which is not in that listing but is always part of
        the benchmark.
        """
        if self.models_input_file:
            self.models_uids = read_uids_file(self.models_input_file)

        if self.models_uids == [self.benchmark.reference_model]:
            # avoid the need of sending a request to the server for
            # finding the benchmark's associated models
            return

        if self.models_uids is None:
            self.models_uids = Benchmark.get_models_uids(self.benchmark_uid)
            self.models_uids.append(self.benchmark.reference_model)
            return

        self.__validate_models()

    def experiments(self) -> List[Experiment]:
        return [
            Experiment(dataset=self.dataset, model=Model.get(model_uid))
            for model_uid in self.models_uids
        ]

    def __validate_models(self):
        benchmark_models = set(Benchmark.get_models_uids(self.benchmark_uid))
        benchmark_models.add(self.benchmark.reference_model)

        non_assoc_models = set(self.models_uids).difference(benchmark_models)
        if non_assoc_models:
            named = ", ".join(str(uid) for uid in sorted(non_assoc_models))
            subject = (
                f"Models of UIDs {named} are"
                if len(non_assoc_models) > 1
                else f"Model of UID {named} is"
            )
            raise InvalidArgumentError(
                f"{subject} not associated with the specified benchmark."
            )
