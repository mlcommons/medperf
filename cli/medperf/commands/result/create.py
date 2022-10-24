import os
from medperf.entities.result import Result
from medperf.enums import Status
import logging

from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.utils import (
    check_cube_validity,
    init_storage,
    pretty_error,
    results_path,
    storage_path,
    cleanup,
)
import medperf.config as config
import yaml


class BenchmarkExecution:
    @classmethod
    def run(
        cls, benchmark_uid: int, data_uid: str, model_uid: int, run_test=False,
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution = cls(benchmark_uid, data_uid, model_uid, run_test)
        execution.prepare()
        execution.validate()
        with execution.ui.interactive():
            execution.get_cubes()
            execution.run_cubes()
        execution.write()
        execution.remove_temp_results()

    def __init__(
        self, benchmark_uid: int, data_uid: int, model_uid: int, run_test=False,
    ):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.model_uid = model_uid
        self.comms = config.comms
        self.ui = config.ui
        self.evaluator = None
        self.model_cube = None
        self.run_test = run_test

    def prepare(self):
        init_storage()
        # If not running the test, redownload the benchmark
        update_bmk = not self.run_test
        self.benchmark = Benchmark.get(self.benchmark_uid, force_update=update_bmk)
        self.ui.print(f"Benchmark Execution: {self.benchmark.name}")
        self.dataset = Dataset.from_generated_uid(self.data_uid)
        if not self.run_test:
            self.out_path = results_path(
                self.benchmark_uid, self.model_uid, self.dataset.uid
            )
        else:
            self.out_path = results_path(
                self.benchmark_uid, self.model_uid, self.dataset.generated_uid
            )

    def validate(self):
        dset_prep_cube = str(self.dataset.preparation_cube_uid)
        bmark_prep_cube = str(self.benchmark.data_preparation)

        if self.dataset.uid is None and not self.run_test:
            msg = "The provided dataset is not registered."
            pretty_error(msg)

        if dset_prep_cube != bmark_prep_cube:
            msg = "The provided dataset is not compatible with the specified benchmark."
            pretty_error(msg)

        in_assoc_cubes = self.model_uid in self.benchmark.models
        if not self.run_test and not in_assoc_cubes:
            pretty_error("The provided model is not part of the specified benchmark.")

    def get_cubes(self):
        evaluator_uid = self.benchmark.evaluator
        self.evaluator = self.__get_cube(evaluator_uid, "Evaluator")
        self.model_cube = self.__get_cube(self.model_uid, "Model")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving {name} cube"
        cube = Cube.get(uid)
        self.ui.print(f"> {name} cube download complete")
        check_cube_validity(cube)
        return cube

    def run_cubes(self):
        infer_timeout = config.infer_timeout
        evaluate_timeout = config.evaluate_timeout
        self.ui.text = "Running model inference on dataset"
        model_uid = str(self.model_cube.uid)
        data_uid = str(self.dataset.generated_uid)
        preds_path = os.path.join(config.predictions_storage, model_uid, data_uid)
        preds_path = storage_path(preds_path)
        data_path = self.dataset.data_path
        out_path = os.path.join(self.out_path, config.results_filename)
        labels_path = self.dataset.labels_path
        try:
            self.model_cube.run(
                task="infer",
                timeout=infer_timeout,
                data_path=data_path,
                output_path=preds_path,
            )
            self.ui.print("> Model execution complete")

            self.ui.text = "Evaluating results"
            self.evaluator.run(
                task="evaluate",
                timeout=evaluate_timeout,
                predictions=preds_path,
                labels=labels_path,
                output_path=out_path,
            )
        except RuntimeError as e:
            logging.error(f"MLCube Execution failed: {e}")
            cleanup([preds_path, out_path])
            pretty_error("Benchmark execution failed")

    def todict(self):
        data_uid = self.dataset.generated_uid if self.run_test else self.dataset.uid

        return {
            "id": None,
            "name": f"{self.benchmark_uid}_{self.model_uid}_{data_uid}",
            "owner": None,
            "benchmark": self.benchmark_uid,
            "model": self.model_uid,
            "dataset": data_uid,
            "results": self.get_temp_results(),
            "metadata": {},
            "approval_status": Status.PENDING.value,
            "approved_at": None,
            "created_at": None,
            "modified_at": None,
        }

    def get_temp_results(self):
        path = os.path.join(self.out_path, config.results_filename)
        with open(path, "r") as f:
            results = yaml.safe_load(f)
        return results

    def remove_temp_results(self):
        path = os.path.join(self.out_path, config.results_filename)
        os.remove(path)

    def write(self):
        results_info = self.todict()
        result = Result(results_info)
        result.write()
