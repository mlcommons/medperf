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
)
from medperf.config import config
from medperf.entities import Result


class BenchmarkExecution:
    @staticmethod
    def run(benchmark_uid: int, data_uid: int, model_uid: int, comms: Comms, ui: UI):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (int): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        init_storage()

        # Ensure user can access the specified benchmark
        if not comms.authorized_by_role(benchmark_uid, "DATA_OWNER"):
            pretty_error("You're not associated to the benchmark as a data owner")
        benchmark = Benchmark.get(benchmark_uid, comms)
        ui.print(f"Benchmark Execution: {benchmark.name}")
        dataset = Dataset(data_uid)

        # Validate Execution
        if dataset.preparation_cube_uid != benchmark.data_preparation:
            pretty_error(
                "The provided dataset is not compatible with the specified benchmark."
            )

        if model_uid not in benchmark.models:
            pretty_error("The provided model is not part of the specified benchmark.")

        cube_uid = benchmark.evaluator
        with ui.interactive() as ui:
            ui.text = "Retrieving evaluator cube"
            # Get cubes
            evaluator = Cube.get(cube_uid, comms)
            ui.print("> Evaluator cube download complete")

            check_cube_validity(evaluator, ui)

            ui.text = "Retrieving model cube. This could take a while..."
            model_cube = Cube.get(model_uid, comms)
            check_cube_validity(model_cube, ui)

            ui.text = "Running model inference on dataset"
            out_path = config["model_output"]
            model_cube.run(
                ui, task="infer", data_path=dataset.data_path, output_path=out_path
            )
            ui.print("> Model execution complete")

            cube_root = str(Path(model_cube.cube_path).parent)
            workspace_path = os.path.join(cube_root, "workspace")
            abs_preds_path = os.path.join(workspace_path, out_path)
            labels_path = os.path.join(dataset.data_path, "data.csv")

            ui.text = "Evaluating results"
            out_path = config["results_storage"]
            out_path = os.path.join(
                out_path, str(benchmark.uid), str(model_uid), str(dataset.data_uid)
            )
            out_path = os.path.join(out_path, "results.yaml")
            evaluator.run(
                ui,
                task="evaluate",
                preds_csv=abs_preds_path,
                labels_csv=labels_path,
                output_path=out_path,
            )

            result = Result(out_path, benchmark.uid, dataset.data_uid, model_uid)
        approved = result.request_approval(ui)
        with ui.interactive() as ui:
            if approved:
                ui.print("Uploading")
                result.upload(comms)
            else:
                pretty_error(
                    "Results upload operation cancelled", ui, add_instructions=False
                )
            cleanup()

