import os
import typer
from yaspin import yaspin

from medperf.entities import Benchmark, Cube, Registration, Server
from medperf.config import config
from medperf.decorators import authenticate
from medperf.utils import (
    check_cube_validity,
    generate_tmp_datapath,
    init_storage,
    cleanup,
    pretty_error,
)


class DataPreparation:
    @staticmethod
    @authenticate
    def run(benchmark_uid: str, data_path: str, labels_path: str, server: Server):
        """Data Preparation flow.

        Args:
            benchmark_uid (str): UID of the desired benchmark.
            data_path (str): Location of the data to be prepared.
            labels_path (str): Labels file location.
        """
        data_path = os.path.abspath(data_path)
        labels_path = os.path.abspath(labels_path)
        out_path, out_datapath = generate_tmp_datapath()
        init_storage()

        # Ensure user can access the specified benchmark
        if not server.authorized_by_role(benchmark_uid, "DATA_OWNER"):
            pretty_error("You're not associated to the benchmark as a data owner")
        benchmark = Benchmark.get(benchmark_uid, server)
        typer.echo(f"Benchmark Data Preparation: {benchmark.name}")

        cube_uid = benchmark.data_preparation
        with yaspin(
            text=f"Retrieving data preparation cube: '{cube_uid}'", color="green"
        ) as sp:
            cube = Cube.get(cube_uid, server)
            sp.write("> Preparation cube download complete")

            check_cube_validity(cube, sp)

            sp.text = f"Running preparation step..."
            cube.run(
                sp,
                task="prepare",
                data_path=data_path,
                labels_path=labels_path,
                output_path=out_datapath,
            )
            sp.write("> Cube execution complete")

            sp.text = "Running sanity check..."
            cube.run(sp, task="sanity_check", data_path=out_datapath)
            sp.write("> Sanity checks complete")

            sp.text = "Generating statistics..."
            cube.run(sp, task="statistics", data_path=out_datapath)
            sp.write("> Statistics complete")

            sp.text = "Starting registration procedure"
            registration = Registration(cube)
            registration.generate_uid(out_datapath)
            if registration.is_registered():
                pretty_error(
                    "This dataset has already been registered. Cancelling submission"
                )

            with sp.hidden():
                approved = registration.request_approval()
                if approved:
                    registration.retrieve_additional_data()
                else:
                    pretty_error(
                        "Registration operation cancelled", add_instructions=False
                    )

            registration.write(out_path)
            sp.write("Uploading")
            data_uid = registration.upload(server)
            registration.to_permanent_path(out_path, data_uid)
            cleanup()
            return data_uid
