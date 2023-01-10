import os
from medperf.entities.result import Result
from medperf.enums import Status
import logging
from tabulate import tabulate

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.utils import (
    check_cube_validity,
    storage_path,
    cleanup_path,
)
import medperf.config as config
from medperf.exceptions import InvalidArgumentError, ExecutionError, InvalidEntityError
import yaml


class BenchmarkExecution:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        data_uid: str,
        models_uids: int,
        run_test=False,
        ignore_errors=False,
        show_summary=False,
        ignore_failed_experiments=False,
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution = cls(
            benchmark_uid,
            data_uid,
            models_uids,
            run_test,
            ignore_errors,
            show_summary,
            ignore_failed_experiments,
        )
        execution.prepare()
        execution.validate()
        with execution.ui.interactive():
            execution.get_cubes()
            execution.run_experiments()
        execution.print_summary()
        return execution.summary

    def __init__(
        self,
        benchmark_uid: int,
        data_uid: int,
        models_uids: int,
        run_test=False,
        ignore_errors=False,
        show_summary=False,
        ignore_failed_experiments=False,
    ):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.models_uids = models_uids
        self.comms = config.comms
        self.ui = config.ui
        self.evaluator = None
        self.models_cubes = []
        self.run_test = run_test
        self.ignore_errors = ignore_errors
        self.ignore_failed_experiments = ignore_failed_experiments
        self.show_summary = show_summary
        self.summary = {}

    def prepare(self):
        # If not running the test, redownload the benchmark
        self.benchmark = Benchmark.get(self.benchmark_uid)
        self.ui.print(f"Benchmark Execution: {self.benchmark.name}")
        self.dataset = Dataset.get(self.data_uid)
        if self.models_uids is None:
            self.models_uids = self.__get_pending_models_uids()

        self.summary = {
            str(model_uid): {
                "success": False,
                "partial": False,
                "error": "",
                "result_uid": None,
            }
            for model_uid in self.models_uids
        }

    def __get_pending_models_uids(self):
        results = Result.all()
        benchmark_dset_results = [
            result
            for result in results
            if result.benchmark_uid == self.benchmark_uid
            and result.dataset_uid == self.data_uid
        ]
        done_models_uids = [result.model_uid for result in benchmark_dset_results]
        pending_models_uids = [
            model for model in self.benchmark.models if model not in done_models_uids
        ]
        return pending_models_uids

    def validate(self):
        dset_prep_cube = str(self.dataset.preparation_cube_uid)
        bmark_prep_cube = str(self.benchmark.data_preparation)

        if self.dataset.uid is None and not self.run_test:
            msg = "The provided dataset is not registered."
            raise InvalidArgumentError(msg)

        if dset_prep_cube != bmark_prep_cube:
            msg = "The provided dataset is not compatible with the specified benchmark."
            raise InvalidArgumentError(msg)

        in_assoc_cubes = set(self.models_uids).issubset(set(self.benchmark.models))
        if not self.run_test and not in_assoc_cubes:
            msg = "Some of the provided models is not part of the specified benchmark."
            raise InvalidArgumentError(msg)

    def get_cubes(self):
        evaluator_uid = self.benchmark.evaluator
        self.evaluator = self.__get_cube(evaluator_uid, "Evaluator")
        self.models_cubes = []
        for model_uid in self.models_uids:
            try:
                model_cube = self.__get_cube(model_uid, "Model")
                self.models_cubes.append(model_cube)
            except InvalidEntityError as e:
                config.ui.print_error(
                    f"There was an error when retrieving the model mlcube {model_uid}: {e}"
                )
                if not self.ignore_failed_experiments:
                    raise e
                self.summary[str(model_uid)]["error"] = str(e)

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving {name} cube"
        cube = Cube.get(uid)
        self.ui.print(f"> {name} cube download complete")
        check_cube_validity(cube)
        return cube

    def run_experiments(self):
        results_uids = []
        for model_cube in self.models_cubes:
            model_uid = str(model_cube.uid)
            try:
                self.run_experiment(model_cube)
            except ExecutionError as e:
                config.ui.print_error(
                    f"There was an error when executing the benchmark with the model {model_uid}: {e}"
                )
                if not self.ignore_failed_experiments:
                    raise e
                self.summary[model_uid]["error"] = str(e)
                results_uids.append(None)
                continue
            result_uid = self.write(model_uid)
            self.summary[model_uid]["result_uid"] = result_uid

            self.remove_temp_results(model_uid)
            self.summary[model_uid]["success"] = True

    def run_experiment(self, model_cube):
        infer_timeout = config.infer_timeout
        evaluate_timeout = config.evaluate_timeout
        self.ui.text = "Running model inference on dataset"
        model_uid = str(model_cube.uid)
        data_uid = str(self.dataset.uid)
        preds_path = os.path.join(config.predictions_storage, model_uid, data_uid)
        preds_path = storage_path(preds_path)
        data_path = self.dataset.data_path
        out_path = self.result_out_path(model_uid)
        labels_path = self.dataset.labels_path
        try:
            model_cube.run(
                task="infer",
                timeout=infer_timeout,
                data_path=data_path,
                output_path=preds_path,
                string_params={"Ptasks.infer.parameters.input.data_path.opts": "ro"},
            )
            self.ui.print("> Model execution complete")

        except ExecutionError as e:
            if not self.ignore_errors:
                logging.error(f"Model MLCube Execution failed: {e}")
                cleanup_path(preds_path)
                raise ExecutionError("Model MLCube failed")
            else:
                self.summary[model_uid]["partial"] = True
                logging.warning(f"Model MLCube Execution failed: {e}")
        try:
            self.ui.text = "Evaluating results"
            self.evaluator.run(
                task="evaluate",
                timeout=evaluate_timeout,
                predictions=preds_path,
                labels=labels_path,
                output_path=out_path,
                string_params={
                    "Ptasks.evaluate.parameters.input.predictions.opts": "ro",
                    "Ptasks.evaluate.parameters.input.labels.opts": "ro",
                },
            )
        except ExecutionError as e:
            logging.error(f"Metrics MLCube Execution failed: {e}")
            cleanup_path(preds_path)
            cleanup_path(out_path)
            raise ExecutionError("Metrics MLCube failed")

    def result_out_path(self, model_uid):
        dset_uid = self.dataset.generated_uid
        result_uid = f"b{self.benchmark_uid}m{model_uid}d{dset_uid}"
        out_path = os.path.join(
            storage_path(config.results_storage), result_uid, config.results_filename
        )
        return out_path

    def todict(self, model_uid):
        metadata = {"partial": self.summary[model_uid]["partial"]}
        return {
            "id": None,
            "name": f"b{self.benchmark_uid}m{model_uid}d{self.data_uid}",
            "owner": None,
            "benchmark": self.benchmark_uid,
            "model": model_uid,
            "dataset": self.data_uid,
            "results": self.get_temp_results(model_uid),
            "metadata": metadata,
            "approval_status": Status.PENDING.value,
            "approved_at": None,
            "created_at": None,
            "modified_at": None,
        }

    def get_temp_results(self, model_uid):
        path = self.result_out_path(model_uid)
        with open(path, "r") as f:
            results = yaml.safe_load(f)
        return results

    def remove_temp_results(self, model_uid):
        path = self.result_out_path(model_uid)
        os.remove(path)

    def write(self, model_uid):
        results_info = self.todict(model_uid)
        result = Result(results_info)
        result.write()
        return result.generated_uid

    def print_summary(self):
        if self.show_summary:

            num_total = len(self.benchmark.models)
            num_success = sum([exp_summary["success"] for exp_summary in self.summary])
            num_failed = len(self.summary) - num_success
            num_skipped = num_total - num_success - num_failed

            num_partial = sum(
                [exp_summary["partial"] is True for exp_summary in self.summary]
            )

            headers = ["model", "success", "partial", "error"]
            data = [
                [exp_summary[key] for key in headers] for exp_summary in self.summary
            ]
            tab = tabulate(data, headers=headers)

            msg = f"Total benchmark models: {num_total}\n"
            msg += f"\t{num_skipped} were skipped (already executed)\n"
            msg += f"\t{num_failed} failed\n"
            msg += f"\t{num_success} ran successfully, with {num_partial} partial results\n"

            config.ui.print(tab)
            config.ui.print(msg)
