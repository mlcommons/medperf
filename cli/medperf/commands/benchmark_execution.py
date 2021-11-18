import os
from pathlib import Path

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Benchmark, Dataset, Cube
from medperf.utils import (
    check_cube_validity,
    init_storage,
    pretty_error,
    cleanup,
    results_path,
)
from medperf.config import config
from medperf.entities import Result


class BenchmarkExecution:
    @classmethod
    def run(
        cls, benchmark_uid: int, data_uid: str, model_uid: int, comms: Comms, ui: UI
    ):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (str): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        execution = cls(benchmark_uid, data_uid, model_uid, comms, ui)
        execution.validate()
        with execution.ui.interactive():
            execution.get_cubes()
            execution.run_cubes()
        cleanup()

    def __init__(
        self, benchmark_uid: int, data_uid: int, model_uid: int, comms: Comms, ui: UI
    ):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.model_uid = model_uid
        self.comms = comms
        self.ui = ui
        self.evaluator = None
        self.model_cube = None

        init_storage()
        self.benchmark = Benchmark.get(benchmark_uid, comms)
        ui.print(f"Benchmark Execution: {self.benchmark.name}")
        self.dataset = Dataset(data_uid, ui)

    def validate(self):
        dset_prep_cube = self.dataset.preparation_cube_uid
        bmark_prep_cube = self.benchmark.data_preparation

        if dset_prep_cube != bmark_prep_cube:
            msg = "The provided dataset is not compatible with the specified benchmark."
            pretty_error(msg, self.ui)

        if self.model_uid not in self.benchmark.models:
            pretty_error(
                "The provided model is not part of the specified benchmark.", self.ui
            )

    def get_cubes(self):
        evaluator_uid = self.benchmark.evaluator
        self.evaluator = self.__get_cube(evaluator_uid, "Evaluator")
        self.model_cube = self.__get_cube(self.model_uid, "Model")

    def __get_cube(self, uid: int, name: str) -> Cube:
        self.ui.text = f"Retrieving {name} cube"
        cube = Cube.get(uid, self.comms)
        self.ui.print(f"> {name} cube download complete")
        check_cube_validity(cube, self.ui)
        return cube

    def run_cubes(self):
        self.ui.text = "Running model inference on dataset"
        out_path = config["model_output"]
        data_path = self.dataset.data_path
        self.model_cube.run(
            self.ui, task="infer", data_path=data_path, output_path=out_path
        )
        self.ui.print("> Model execution complete")

        cube_path = self.model_cube.cube_path
        cube_root = str(Path(cube_path).parent)
        workspace_path = os.path.join(cube_root, "workspace")
        abs_preds_path = os.path.join(workspace_path, out_path)
        labels_path = os.path.join(data_path, "data.csv")

        self.ui.text = "Evaluating results"
        out_path = results_path(self.benchmark_uid, self.model_uid, self.data_uid)
        self.evaluator.run(
            self.ui,
            task="evaluate",
            preds_csv=abs_preds_path,
            labels_csv=labels_path,
            output_path=out_path,
        )
