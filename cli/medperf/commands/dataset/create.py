import os

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Benchmark, Cube, Registration
from medperf.utils import (
    check_cube_validity,
    generate_tmp_datapath,
    init_storage,
    cleanup,
    pretty_error,
)


class DataPreparation:
    @classmethod
    def run(
        cls, benchmark_uid: str, data_path: str, labels_path: str, comms: Comms, ui: UI
    ):
        preparation = cls(benchmark_uid, data_path, labels_path, comms, ui)
        with preparation.ui.interactive():
            preparation.get_prep_cube()
            preparation.run_cube_tasks()
        data_uid = preparation.create_registration()
        cleanup()
        return data_uid

    def __init__(
        self, benchmark_uid: str, data_path: str, labels_path: str, comms: Comms, ui: UI
    ):
        self.comms = comms
        self.ui = ui
        self.data_path = os.path.abspath(data_path)
        self.labels_path = os.path.abspath(labels_path)
        out_path, out_datapath = generate_tmp_datapath()
        self.out_path = out_path
        self.out_datapath = out_datapath
        init_storage()

        self.benchmark = Benchmark.get(benchmark_uid, comms)
        self.ui.print(f"Benchmark Data Preparation: {self.benchmark.name}")

    def get_prep_cube(self):
        cube_uid = self.benchmark.data_preparation
        self.ui.text = f"Retrieving data preparation cube: '{cube_uid}'"
        self.cube = Cube.get(cube_uid, self.comms)
        self.ui.print("> Preparation cube download complete")
        check_cube_validity(self.cube, self.ui)

    def run_cube_tasks(self):
        data_path = self.data_path
        labels_path = self.labels_path
        out_datapath = self.out_datapath

        self.ui.text = "Running preparation step..."
        self.cube.run(
            self.ui,
            task="prepare",
            data_path=data_path,
            labels_path=labels_path,
            output_path=out_datapath,
        )
        self.ui.print("> Cube execution complete")

        self.ui.text = "Running sanity check..."
        self.cube.run(self.ui, task="sanity_check", data_path=out_datapath)
        self.ui.print("> Sanity checks complete")

        self.ui.text = "Generating statistics..."
        self.cube.run(self.ui, task="statistics", data_path=out_datapath)
        self.ui.print("> Statistics complete")

    def create_registration(self):
        self.registration = Registration(self.cube)
        self.registration.generate_uids(self.data_path, self.out_datapath)
        self.registration.retrieve_additional_data(self.ui)
        self.registration.to_permanent_path(self.out_path)
        self.registration.write()
        return self.registration.generated_uid
