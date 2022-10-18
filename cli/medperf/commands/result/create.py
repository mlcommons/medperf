import os

from medperf.ui.interface import UI
from medperf.comms.interface import Comms
from medperf.entities.cube import Cube
from medperf.entities.dataset import Dataset
from medperf.entities.benchmark import Benchmark
from medperf.utils import (
    check_cube_validity,
    init_storage,
    pretty_error,
    results_path,
    storage_path,
)
import medperf.config as config


class BenchmarkExecution:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        data_uid: str,
        model_uid: int,
        comms: Comms,
        ui: UI,
        run_test=False,
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution = cls(benchmark_uid, data_uid, model_uid, comms, ui, run_test)
        execution.prepare()
        execution.validate()
        with execution.ui.interactive():
            execution.get_cubes()
            execution.run_cubes()

    def __init__(
        self,
        benchmark_uid: int,
        data_uid: int,
        model_uid: int,
        comms: Comms,
        ui: UI,
        run_test=False,
    ):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.model_uid = model_uid
        self.comms = comms
        self.ui = ui
        self.evaluator = None
        self.model_cube = None
        self.run_test = run_test

    def prepare(self):
        init_storage()
        # If not running the test, redownload the benchmark
        update_bmk = not self.run_test
        self.benchmark = Benchmark.get(self.benchmark_uid, force_update=update_bmk)
        self.ui.print(f"Benchmark Execution: {self.benchmark.name}")
        self.dataset = Dataset(self.data_uid)

    def validate(self):
        dset_prep_cube = str(self.dataset.preparation_cube_uid)
        bmark_prep_cube = str(self.benchmark.data_preparation)

        if self.dataset.uid is None and not self.run_test:
            msg = "The provided dataset is not registered."
            pretty_error(msg, self.ui)

        if dset_prep_cube != bmark_prep_cube:
            msg = "The provided dataset is not compatible with the specified benchmark."
            pretty_error(msg, self.ui)

        in_assoc_cubes = self.model_uid in self.benchmark.models
        if not self.run_test and not in_assoc_cubes:
            pretty_error(
                "The provided model is not part of the specified benchmark.", self.ui
            )

    def get_cubes(self):
        evaluator_uid = self.benchmark.evaluator
        self.evaluator = self.__get_cube(evaluator_uid, "Evaluator")
        self.model_cube = self.__get_cube(self.model_uid, "Model")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving {name} cube"
        cube = Cube.get(uid)
        self.ui.print(f"> {name} cube download complete")
        check_cube_validity(cube, self.ui)
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
        self.model_cube.run(
            self.ui,
            task="infer",
            timeout=infer_timeout,
            data_path=data_path,
            output_path=preds_path,
            string_params={
                "Ptasks.infer.parameters.input.data_path.opts": "ro"
            },
        )
        self.ui.print("> Model execution complete")

        labels_path = self.dataset.labels_path

        self.ui.text = "Evaluating results"
        if not self.run_test:
            out_path = results_path(
                self.benchmark_uid, self.model_uid, self.dataset.uid
            )
        else:
            out_path = results_path(
                self.benchmark_uid, self.model_uid, self.dataset.generated_uid
            )

        self.evaluator.run(
            self.ui,
            task="evaluate",
            timeout=evaluate_timeout,
            predictions=preds_path,
            labels=labels_path,
            output_path=out_path,
            string_params={
                "Ptasks.evaluate.parameters.input.predictions.opts": "ro",
                "Ptasks.evaluate.parameters.input.labels.opts": "ro"
            }
        )
