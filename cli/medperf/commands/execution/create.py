import os
from typing import List, Optional
from medperf.account_management.account_management import get_medperf_user_data
from medperf.commands.execution.execution_flow import ExecutionFlow
from medperf.entities.execution import Execution
from tabulate import tabulate
from medperf.commands.execution.utils import filter_latest_executions

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
import medperf.config as config
from medperf.exceptions import (
    InvalidArgumentError,
    ExecutionError,
    InvalidEntityError,
    MedperfException,
)


class BenchmarkExecution:
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
    ):
        """Benchmark execution flow.
        How the following variables affect whether to execute or no:
        no_cache, rerun_finalized_executions, and
        execution object state ((0) doesn't exist, (1) exist, (2) executed, (3) finalized):

        if no_cache is false and rerun_finalized_executions is false, then execute if (0) or (1)
        if no_cache is true and rerun_finalized_executions is false, then execute if (0) or (1) or(2)
        if no_cache is true and rerun_finalized_executions is true, then execute anyway


        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            models_uids (List|None): list of model UIDs to execute.
                                    if None, models_input_file will be used
            models_input_file: filename to read from
            if models_uids and models_input_file are None, use all benchmark models
        """
        if rerun_finalized_executions:
            no_cache = True
        execution_flow = cls(
            benchmark_uid,
            data_uid,
            models_uids,
            models_input_file,
            ignore_model_errors,
            ignore_failed_experiments,
            no_cache,
            rerun_finalized_executions,
        )
        with execution_flow.ui.interactive():
            execution_flow.prepare()
        execution_flow.validate()
        execution_flow.prepare_models()
        execution_flow.load_existing_executions()
        with execution_flow.ui.interactive():
            executions = execution_flow.run_experiments()
        if show_summary:
            execution_flow.print_summary()
        return executions

    def __init__(
        self,
        benchmark_uid: int,
        data_uid: int,
        models_uids,
        models_input_file: str = None,
        ignore_model_errors=False,
        ignore_failed_experiments=False,
        no_cache=False,
        rerun_finalized_executions=False,
    ):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.models_uids = models_uids
        self.models_input_file = models_input_file
        self.ui = config.ui
        self.evaluator = None
        self.ignore_model_errors = ignore_model_errors
        self.ignore_failed_experiments = ignore_failed_experiments
        self.existing_executions = {}
        self.experiments = []
        self.no_cache = no_cache
        self.rerun_finalized_executions = rerun_finalized_executions

    def prepare(self):
        self.benchmark = Benchmark.get(self.benchmark_uid)
        self.ui.print(f"Benchmark Execution: {self.benchmark.name}")
        self.dataset = Dataset.get(self.data_uid)
        evaluator_uid = self.benchmark.data_evaluator_mlcube
        self.evaluator = self.__get_cube(evaluator_uid, "Evaluator")

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
        if self.models_input_file:
            self.models_uids = self.__get_models_from_file()

        if self.models_uids == [self.benchmark.reference_model_mlcube]:
            # avoid the need of sending a request to the server for
            # finding the benchmark's associated models
            return

        benchmark_models = Benchmark.get_models_uids(self.benchmark_uid)
        benchmark_models.append(self.benchmark.reference_model_mlcube)

        if self.models_uids is None:
            self.models_uids = benchmark_models
        else:
            self.__validate_models(benchmark_models)

    def __get_models_from_file(self):
        if not os.path.exists(self.models_input_file):
            raise InvalidArgumentError("The given file does not exist")
        with open(self.models_input_file) as f:
            text = f.read()
        models = text.strip().split(",")
        try:
            return list(map(int, models))
        except ValueError as e:
            msg = f"Could not parse the given file: {e}. "
            msg += "The file should contain a list of comma-separated integers"
            raise InvalidArgumentError(msg)

    def __validate_models(self, benchmark_models):
        models_set = set(self.models_uids)
        benchmark_models_set = set(benchmark_models)
        non_assoc_cubes = models_set.difference(benchmark_models_set)
        if non_assoc_cubes:
            if len(non_assoc_cubes) > 1:
                msg = f"Model of UID {non_assoc_cubes} is not associated with the specified benchmark."
            else:
                msg = f"Models of UIDs {non_assoc_cubes} are not associated with the specified benchmark."
            raise InvalidArgumentError(msg)

    def load_existing_executions(self):
        user_id = get_medperf_user_data()["id"]
        executions = Execution.all(filters={"owner": user_id})
        benchmark_dset_executions = [
            execution
            for execution in executions
            if execution.benchmark == self.benchmark_uid
            and execution.dataset == self.data_uid
        ]
        benchmark_dset_executions = filter_latest_executions(benchmark_dset_executions)
        self.existing_executions = {
            execution.model: execution for execution in benchmark_dset_executions
        }

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving container '{name}'"
        cube = Cube.get(uid)
        cube.download_run_files()
        self.ui.print(f"> Container '{name}' download complete")
        return cube

    def run_experiments(self) -> list[Execution]:
        for model_uid in self.models_uids:
            execution = self.existing_executions.get(model_uid, None)
            if (
                execution is None
                or execution.finalized
                and self.rerun_finalized_executions
            ):
                execution = self.__create_execution(model_uid)

            if self.rerun_finalized_executions:
                should_run = True
            else:
                if self.no_cache:
                    should_run = not execution.finalized
                else:
                    should_run = not execution.is_executed()

            if should_run:
                execution.unmark_as_executed()
            else:
                self.experiments.append(
                    {
                        "model_uid": model_uid,
                        "execution": execution,
                        "cached": True,
                        "error": "",
                        "partial": execution.is_partial(),
                    }
                )
                continue

            try:
                model_cube = self.__get_cube(model_uid, "Model")
                execution_summary = ExecutionFlow.run(
                    dataset=self.dataset,
                    model=model_cube,
                    evaluator=self.evaluator,
                    execution=execution,
                    ignore_model_errors=self.ignore_model_errors,
                )
            except MedperfException as e:
                self.__handle_experiment_error(model_uid, e)
                self.experiments.append(
                    {
                        "model_uid": model_uid,
                        "execution": None,
                        "cached": False,
                        "error": str(e),
                        "partial": "N/A",
                    }
                )
                continue

            execution.mark_as_executed()
            execution.save_results(
                execution_summary["results"], execution_summary["partial"]
            )

            self.experiments.append(
                {
                    "model_uid": model_uid,
                    "execution": execution,
                    "cached": False,
                    "error": "",
                    "partial": execution_summary["partial"],
                }
            )
        return [experiment["execution"] for experiment in self.experiments]

    def __handle_experiment_error(self, model_uid, exception):
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

    def __create_execution(self, model_uid: int) -> Execution:
        # Get or create an execution object on the server
        query_dict = {
            "dataset": self.data_uid,
            "model": model_uid,
            "benchmark": self.benchmark_uid,
            "name": self.__execution_name(model_uid),
        }
        execution = Execution(**query_dict)
        updated_exec_dict = execution.upload()
        execution = Execution(**updated_exec_dict)
        execution.write()
        return execution

    def __execution_name(self, model_uid):
        return f"b{self.benchmark_uid}m{model_uid}d{self.data_uid}"

    def print_summary(self):
        headers = ["model", "Execution UID", "partial result", "from cache", "error"]
        data_lists_for_display = []

        num_total = len(self.experiments)
        num_success_run = 0
        num_failed = 0
        num_skipped = 0
        num_partial_skipped = 0
        num_partial_run = 0
        for experiment in self.experiments:
            # populate display data
            if experiment["execution"]:
                data_lists_for_display.append(
                    [
                        experiment["model_uid"],
                        experiment["execution"].id,
                        experiment["partial"],
                        experiment["cached"],
                        experiment["error"],
                    ]
                )
            else:
                data_lists_for_display.append(
                    [experiment["model_uid"], "", "", "", experiment["error"]]
                )

            # statistics
            if experiment["error"]:
                num_failed += 1
            elif experiment["cached"]:
                num_skipped += 1
                if experiment["partial"]:
                    num_partial_skipped += 1
            elif experiment["execution"]:
                num_success_run += 1
                if experiment["partial"]:
                    num_partial_run += 1

        tab = tabulate(data_lists_for_display, headers=headers)

        msg = f"Total number of models: {num_total}\n"
        msg += f"\t{num_skipped} were skipped (already executed), "
        msg += f"of which {num_partial_run} have partial results\n"
        msg += f"\t{num_failed} failed\n"
        msg += f"\t{num_success_run} ran successfully, "
        msg += f"of which {num_partial_run} have partial results\n"

        config.ui.print(tab)
        config.ui.print(msg)
