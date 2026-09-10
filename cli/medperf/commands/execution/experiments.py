"""Running the (dataset, model) pairs of a benchmark, whoever asked for them.

A data owner runs one dataset against many models; a model owner runs one model
against many datasets. Which pairs those are, and who is allowed to ask for
them, is settled before anything reaches here -- see `dataset_benchmark_run`
and `model_benchmark_run`. What is left over is the same work either way:
reuse or create the execution record, decide whether a cached result still
stands, run the pair, store what came back, and report on it.
"""

from dataclasses import dataclass
from typing import List

from tabulate import tabulate

import medperf.config as config
from medperf.account_management.account_management import get_medperf_user_data
from medperf.commands.execution.execution_flow import ExecutionFlow
from medperf.commands.execution.plan import BenchmarkPlan
from medperf.commands.execution.utils import filter_latest_executions
from medperf.entities.dataset import Dataset
from medperf.entities.execution import Execution
from medperf.entities.model import Model
from medperf.exceptions import (
    ExecutionError,
    InvalidEntityError,
    MedperfException,
)


@dataclass(frozen=True)
class Experiment:
    """One (dataset, model) pair of a benchmark, ready to be run."""

    dataset: Dataset
    model: Model


class ExperimentsRunner:
    """Runs a list of already-resolved pairs of one benchmark.

    Decides nothing about who may run what: both sides of a benchmark hand it
    the pairs they settled on, and it does the same work for either.
    """

    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        plan: BenchmarkPlan,
        experiments: List[Experiment],
        ignore_model_errors: bool = False,
        ignore_failed_experiments: bool = False,
        no_cache: bool = False,
        rerun_finalized_executions: bool = False,
        show_summary: bool = False,
    ) -> List[Execution]:
        """Runs every given pair and returns their executions.

        How the following variables affect whether to execute or no:
        no_cache, rerun_finalized_executions, and
        execution object state ((0) doesn't exist, (1) exist, (2) executed, (3) finalized):

        if no_cache is false and rerun_finalized_executions is false, then execute if (0) or (1)
        if no_cache is true and rerun_finalized_executions is false, then execute if (0) or (1) or(2)
        if no_cache is true and rerun_finalized_executions is true, then execute anyway

        Args:
            benchmark_uid (int): the benchmark the pairs belong to
            plan (BenchmarkPlan): the benchmark's resolved components
            experiments (List[Experiment]): the pairs to run, in order
        """
        runner = cls(
            benchmark_uid,
            plan,
            experiments,
            ignore_model_errors,
            ignore_failed_experiments,
            no_cache,
            rerun_finalized_executions,
        )
        runner.load_existing_executions()
        with runner.ui.interactive():
            executions = runner.run_experiments()
        if show_summary:
            runner.print_summary()
        return executions

    def __init__(
        self,
        benchmark_uid: int,
        plan: BenchmarkPlan,
        experiments: List[Experiment],
        ignore_model_errors: bool = False,
        ignore_failed_experiments: bool = False,
        no_cache: bool = False,
        rerun_finalized_executions: bool = False,
    ):
        self.benchmark_uid = benchmark_uid
        self.plan = plan
        self.experiments = experiments
        self.ui = config.ui
        self.ignore_model_errors = ignore_model_errors
        self.ignore_failed_experiments = ignore_failed_experiments
        # Rerunning something already reported is by definition not reading a
        # cached result, so the two flags cannot disagree.
        self.no_cache = no_cache or rerun_finalized_executions
        self.rerun_finalized_executions = rerun_finalized_executions
        self.existing_executions = {}
        self.reports = []

    def load_existing_executions(self):
        user_id = get_medperf_user_data()["id"]
        executions = Execution.all(filters={"owner": user_id})
        benchmark_executions = [
            execution
            for execution in executions
            if execution.benchmark == self.benchmark_uid
        ]
        benchmark_executions = filter_latest_executions(benchmark_executions)
        self.existing_executions = {
            (execution.dataset, execution.model): execution
            for execution in benchmark_executions
        }

    def run_experiments(self) -> List[Execution]:
        for experiment in self.experiments:
            self.__run_experiment(experiment)
        return [report["execution"] for report in self.reports]

    def __run_experiment(self, experiment: Experiment):
        dataset, model = experiment.dataset, experiment.model
        execution = self.existing_executions.get((dataset.id, model.id), None)
        # A reported execution is not edited: rerunning one is a second run,
        # and it gets a record of its own.
        already_reported = execution is not None and execution.finalized
        if execution is None or (already_reported and self.rerun_finalized_executions):
            execution = self.__create_execution(experiment)

        if self.rerun_finalized_executions:
            should_run = True
        else:
            if self.no_cache:
                should_run = not execution.finalized
            else:
                should_run = not execution.is_executed()

        if not should_run:
            self.__report(
                experiment,
                execution=execution,
                cached=True,
                partial=execution.is_partial(),
                confidential="N/A",
            )
            return

        execution.unmark_as_executed()
        try:
            execution_summary = ExecutionFlow.run(
                plan=self.plan,
                dataset=dataset,
                model=model,
                execution=execution,
                ignore_model_errors=self.ignore_model_errors,
            )
        except MedperfException as e:
            self.__handle_experiment_error(experiment, e)
            self.__report(
                experiment,
                execution=None,
                error=str(e),
                partial="N/A",
                confidential=model.requires_cc(),
            )
            return

        execution.mark_as_executed()
        execution.save_results(
            execution_summary["results"],
            execution_summary["partial"],
            # Only a confidential execution can produce one. Everything else
            # leaves it empty, which is what "unverified" looks like.
            execution_summary.get("integrity_proof", {}),
        )
        self.__report(
            experiment,
            execution=execution,
            partial=execution_summary["partial"],
            confidential=model.requires_cc(),
        )

    def __report(
        self,
        experiment: Experiment,
        execution,
        cached=False,
        error="",
        partial=False,
        confidential=False,
    ):
        self.reports.append(
            {
                "model_uid": experiment.model.id,
                "dataset_uid": experiment.dataset.id,
                "execution": execution,
                "cached": cached,
                "error": error,
                "partial": partial,
                "confidential": confidential,
            }
        )

    def __handle_experiment_error(self, experiment: Experiment, exception):
        model_uid = experiment.model.id
        if isinstance(exception, InvalidEntityError):
            config.ui.print_error(
                f"There was an error when retrieving the model container {model_uid}: {exception}"
            )
        elif isinstance(exception, ExecutionError):
            config.ui.print_error(
                f"There was an error when executing the benchmark with the model {model_uid}: {exception}"
            )
        else:
            raise exception
        if not self.ignore_failed_experiments:
            raise exception

    def __create_execution(self, experiment: Experiment) -> Execution:
        # Get or create an execution object on the server
        query_dict = {
            "dataset": experiment.dataset.id,
            "model": experiment.model.id,
            "benchmark": self.benchmark_uid,
            "name": self.__execution_name(experiment),
        }
        execution = Execution(**query_dict)
        updated_exec_dict = execution.upload()
        execution = Execution(**updated_exec_dict)
        execution.write()
        return execution

    def __execution_name(self, experiment: Experiment):
        return (
            f"b{self.benchmark_uid}"
            f"m{experiment.model.id}"
            f"d{experiment.dataset.id}"
        )

    def print_summary(self):
        headers = [
            "model",
            "dataset",
            "Execution UID",
            "partial result",
            "from cache",
            "confidential",
            "error",
        ]
        data_lists_for_display = []

        num_total = len(self.reports)
        num_success_run = 0
        num_failed = 0
        num_skipped = 0
        num_partial_skipped = 0
        num_partial_run = 0
        for report in self.reports:
            # populate display data
            if report["execution"]:
                data_lists_for_display.append(
                    [
                        report["model_uid"],
                        report["dataset_uid"],
                        report["execution"].id,
                        report["partial"],
                        report["cached"],
                        report["confidential"],
                        report["error"],
                    ]
                )
            else:
                data_lists_for_display.append(
                    [
                        report["model_uid"],
                        report["dataset_uid"],
                        "",
                        "",
                        "",
                        report["confidential"],
                        report["error"],
                    ]
                )

            # statistics
            if report["error"]:
                num_failed += 1
            elif report["cached"]:
                num_skipped += 1
                if report["partial"]:
                    num_partial_skipped += 1
            elif report["execution"]:
                num_success_run += 1
                if report["partial"]:
                    num_partial_run += 1

        tab = tabulate(data_lists_for_display, headers=headers)

        msg = f"Total number of experiments: {num_total}\n"
        msg += f"\t{num_skipped} were skipped (already executed), "
        msg += f"of which {num_partial_skipped} have partial results\n"
        msg += f"\t{num_failed} failed\n"
        msg += f"\t{num_success_run} ran successfully, "
        msg += f"of which {num_partial_run} have partial results\n"

        config.ui.print(tab)
        config.ui.print(msg)
