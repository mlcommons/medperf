import os

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Benchmark, Cube, Registration
from medperf.config import config
from medperf.utils import (
    check_cube_validity,
    generate_tmp_datapath,
    init_storage,
    cleanup,
    pretty_error,
)


class DataPreparation:
    @staticmethod
    def run(benchmark_uid: str, data_path: str, labels_path: str, comms: Comms, ui: UI):
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

        # Ensure user can access the uiecified benchmark
        if not comms.authorized_by_role(benchmark_uid, "DATA_OWNER"):
            pretty_error("You're not associated to the benchmark as a data owner", ui)
        benchmark = Benchmark.get(benchmark_uid, comms)
        ui.print(f"Benchmark Data Preparation: {benchmark.name}")

        cube_uid = benchmark.data_preparation
        with ui.interactive() as ui:
            ui.text = f"Retrieving data preparation cube: '{cube_uid}'"
            cube = Cube.get(cube_uid, comms)
            ui.print("> Preparation cube download complete")

            check_cube_validity(cube, ui)

            ui.text = f"Running preparation step..."
            cube.run(
                ui,
                task="prepare",
                data_path=data_path,
                labels_path=labels_path,
                output_path=out_datapath,
            )
            ui.print("> Cube execution complete")

            ui.text = "Running sanity check..."
            cube.run(ui, task="sanity_check", data_path=out_datapath)
            ui.print("> Sanity checks complete")

            ui.text = "Generating statistics..."
            cube.run(ui, task="statistics", data_path=out_datapath)
            ui.print("> Statistics complete")

            ui.text = "Starting registration procedure"
            registration = Registration(cube)
            registration.generate_uid(out_datapath)
            if registration.is_registered(ui):
                pretty_error(
                    "This dataset has already been registered. Cancelling submission",
                    ui,
                )

        approved = registration.request_approval(ui)
        if approved:
            registration.retrieve_additional_data(ui)
        else:
            pretty_error("Registration operation cancelled", ui, add_instructions=False)

        with ui.interactive() as ui:
            registration.write(out_path)
            ui.print("Uploading")
            data_uid = registration.upload(comms)
            registration.to_permanent_path(out_path, data_uid)
            cleanup()
            return data_uid
