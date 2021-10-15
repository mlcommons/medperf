import logging
import typer
import os
from pathlib import Path
from yaspin import yaspin

from medperf.entities import Benchmark, Dataset, Cube, Server
from medperf.utils import (
    check_cube_validity,
    init_storage,
    pretty_error,
    cleanup,
)
from medperf.decorators import authenticate
from medperf.config import config
from medperf.entities import Result


class BenchmarkExecution:
    @staticmethod
    @authenticate
    def run(benchmark_uid: int, data_uid: int, model_uid: int, server: Server = None):
        """Benchmark execution flow.

        Args:
            benchmark_uid (int): UID of the desired benchmark
            data_uid (int): Registered Dataset UID
            model_uid (int): UID of model to execute
        """
        # Ensure user can access the specified benchmark
        if not server.authorized_by_role(benchmark_uid, "DATA_OWNER"):
            pretty_error("You're not associated to the benchmark as a data owner")
        benchmark = Benchmark.get(benchmark_uid, server)
        typer.echo(f"Benchmark Execution: {benchmark.name}")
        dataset = Dataset(data_uid)

        if dataset.preparation_cube_uid != benchmark.data_preparation:
            pretty_error(
                "The provided dataset is not compatible with the specified benchmark."
            )

        if model_uid not in benchmark.models:
            pretty_error("The provided model is not part of the specified benchmark.")

        cube_uid = benchmark.evaluator
        with yaspin(text=f"Retrieving evaluator cube", color="green") as sp:
            evaluator = Cube.get(cube_uid, server)
            sp.write("> Evaluator cube download complete")

            check_cube_validity(evaluator, sp)

            sp.text = "Retrieving model cube. This could take a while..."
            model_cube = Cube.get(model_uid, server)
            check_cube_validity(model_cube, sp)

            sp.text = "Running model inference on dataset"
            out_path = config["model_output"]
            model_cube.run(
                sp, task="whatever", data_path=dataset.data_path, output_path=out_path
            )
            sp.write("> Model execution complete")

            cube_root = str(Path(model_cube.cube_path).parent)
            workspace_path = os.path.join(cube_root, "workspace")
            abs_preds_path = os.path.join(workspace_path, out_path)
            labels_path = os.path.join(dataset.data_path, "data.csv")

            sp.text = "Evaluating results"
            out_path = config["results_storage"]
            out_path = os.path.join(
                out_path, str(benchmark.uid), str(model_uid), str(dataset.data_uid)
            )
            out_path = os.path.join(out_path, "results.yaml")
            evaluator.run(
                sp,
                task="evaluate",
                preds_csv=abs_preds_path,
                labels_csv=labels_path,
                output_path=out_path,
            )

            result = Result(out_path, benchmark.uid, dataset.data_uid, model_uid)
            with sp.hidden():
                approved = result.request_approval()
            if approved:
                typer.echo("Uploading")
                result.upload(server)
            else:
                pretty_error("Results upload operation cancelled")
            cleanup()
