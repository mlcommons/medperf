import os
from pathlib import Path

from medperf.ui.interface import UI
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.entities.registration import Registration
from medperf.utils import (
    check_cube_validity,
    generate_tmp_datapath,
    init_storage,
    pretty_error,
)


class DataPreparation:
    @classmethod
    def run(
        cls,
        benchmark_uid: str,
        prep_cube_uid: str,
        data_path: str,
        labels_path: str,
        comms: Comms,
        ui: UI,
        run_test=False,
        name: str = None,
        description: str = None,
        location: str = None,
    ):

        too_many_resources = benchmark_uid and prep_cube_uid
        no_resource = benchmark_uid is None and prep_cube_uid is None
        if no_resource or too_many_resources:
            pretty_error(
                "Invalid arguments. Must provide either a benchmark or a preparation mlcube",
                ui,
            )

        preparation = cls(
            benchmark_uid,
            prep_cube_uid,
            data_path,
            labels_path,
            name,
            description,
            location,
            comms,
            ui,
            run_test,
        )
        preparation.validate()
        with preparation.ui.interactive():
            preparation.get_prep_cube()
            preparation.run_cube_tasks()
        data_uid = preparation.create_registration()
        return data_uid

    def __init__(
        self,
        benchmark_uid: str,
        prep_cube_uid: str,
        data_path: str,
        labels_path: str,
        name: str,
        description: str,
        location: str,
        comms: Comms,
        ui: UI,
        run_test=False,
    ):
        self.comms = comms
        self.ui = ui
        self.data_path = str(Path(data_path).resolve())
        self.labels_path = str(Path(labels_path).resolve())
        out_path = generate_tmp_datapath()
        self.out_path = out_path
        self.name = name
        self.description = description
        self.location = location
        self.out_datapath = os.path.join(out_path, "data")
        self.out_labelspath = os.path.join(out_path, "labels")
        self.labels_specified = False
        self.run_test = run_test
        init_storage()

        if benchmark_uid is not None:
            benchmark = Benchmark.get(benchmark_uid, comms)
            self.cube_uid = benchmark.data_preparation
            self.ui.print(f"Benchmark Data Preparation: {benchmark.name}")
        else:
            self.cube_uid = prep_cube_uid

    def validate(self):
        if not os.path.exists(self.data_path):
            pretty_error("The provided data path doesn't exist", self.ui)
        if not os.path.exists(self.labels_path):
            pretty_error("The provided labels path doesn't exist", self.ui)

    def get_prep_cube(self):
        self.ui.text = f"Retrieving data preparation cube: '{self.cube_uid}'"
        self.cube = Cube.get(self.cube_uid, self.comms, self.ui)
        self.ui.print("> Preparation cube download complete")
        check_cube_validity(self.cube, self.ui)

    def run_cube_tasks(self):
        prepare_timeout = config.prepare_timeout
        sanity_check_timeout = config.sanity_check_timeout
        statistics_timeout = config.statistics_timeout
        data_path = self.data_path
        labels_path = self.labels_path
        out_datapath = self.out_datapath
        out_labelspath = self.out_labelspath

        # Specify parameters for the tasks
        prepare_params = {
            "data_path": data_path,
            "labels_path": labels_path,
            "output_path": out_datapath,
        }

        sanity_params = {
            "data_path": out_datapath,
        }

        statistics_params = {
            "data_path": out_datapath,
        }

        # Check if labels_path is specified
        self.labels_specified = (
            self.cube.get_default_output("prepare", "output_labels_path") is not None
        )
        if self.labels_specified:
            # Add the labels parameter
            prepare_params["output_labels_path"] = out_labelspath
            sanity_params["labels_path"] = out_labelspath
            statistics_params["labels_path"] = out_labelspath

        # Run the tasks
        self.ui.text = "Running preparation step..."
        self.cube.run(
            self.ui, task="prepare", timeout=prepare_timeout, **prepare_params
        )
        self.ui.print("> Cube execution complete")

        self.ui.text = "Running sanity check..."
        self.cube.run(
            self.ui, task="sanity_check", timeout=sanity_check_timeout, **sanity_params
        )
        self.ui.print("> Sanity checks complete")

        self.ui.text = "Generating statistics..."
        self.cube.run(
            self.ui, task="statistics", timeout=statistics_timeout, **statistics_params
        )
        self.ui.print("> Statistics complete")

    def create_registration(self):
        self.registration = Registration(
            self.cube,
            self.name,
            self.description,
            self.location,
            separate_labels=self.labels_specified,
        )
        self.registration.generate_uids(self.data_path, self.out_datapath)

        if self.run_test:
            self.registration.in_uid = (
                config.test_dset_prefix + self.registration.in_uid
            )
            self.registration.generated_uid = (
                config.test_dset_prefix + self.registration.generated_uid
            )

        self.registration.to_permanent_path(self.out_path)
        self.registration.write()
        return self.registration.generated_uid
