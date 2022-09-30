import os
from pathlib import Path
import shutil
from medperf.enums import Status
import yaml
from medperf.ui.interface import UI
import medperf.config as config
from medperf.comms.interface import Comms
from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.utils import (
    check_cube_validity,
    generate_tmp_datapath,
    get_folder_sha1,
    get_stats,
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
        preparation.generate_uids()
        preparation.to_permanent_path()
        preparation.write()
        return preparation.generated_uid

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
        self.benchmark_uid = benchmark_uid
        self.prep_cube_uid = prep_cube_uid
        self.in_uid = None
        self.generated_uid = None
        init_storage()

    def validate(self):
        if not os.path.exists(self.data_path):
            pretty_error("The provided data path doesn't exist", self.ui)
        if not os.path.exists(self.labels_path):
            pretty_error("The provided labels path doesn't exist", self.ui)

        too_many_resources = self.benchmark_uid and self.prep_cube_uid
        no_resource = self.benchmark_uid is None and self.prep_cube_uid is None
        if no_resource or too_many_resources:
            pretty_error(
                "Invalid arguments. Must provide either a benchmark or a preparation mlcube",
                self.ui,
            )

    def get_prep_cube(self):
        cube_uid = self.prep_cube_uid
        if cube_uid is None:
            benchmark = Benchmark.get(self.benchmark_uid, self.comms)
            cube_uid = benchmark.data_preparation
            self.ui.print(f"Benchmark Data Preparation: {benchmark.name}")
        self.ui.text = f"Retrieving data preparation cube: '{cube_uid}'"
        self.cube = Cube.get(cube_uid)
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
        out_statistics_path = os.path.join(self.out_path, config.statistics_filename)

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
            "output_path": out_statistics_path,
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

    def generate_uids(self):
        """Auto-generates dataset UIDs for both input and output paths
        """
        self.in_uid = get_folder_sha1(self.data_path)
        self.generated_uid = get_folder_sha1(self.out_datapath)
        if self.run_test:
            self.in_uid = config.test_dset_prefix + self.in_uid
            self.generated_uid = config.test_dset_prefix + self.generated_uid

    def to_permanent_path(self) -> str:
        """Renames the temporary data folder to permanent one using the hash of
        the registration file
        """
        new_path = os.path.join(str(Path(self.out_path).parent), self.generated_uid)
        if os.path.exists(new_path):
            shutil.rmtree(new_path)
        os.rename(self.out_path, new_path)
        self.out_path = new_path

    def todict(self) -> dict:
        """Dictionary representation of the dataset

        Returns:
            dict: dictionary containing information pertaining the dataset.
        """
        data = {
            "uid": None,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "data_preparation_mlcube": self.cube.uid,
            "input_data_hash": self.in_uid,
            "generated_uid": self.generated_uid,
            "split_seed": 0,  # Currently this is not used
            "generated_metadata": get_stats(self.out_path),
            "status": Status.PENDING.value,
            "state": "OPERATION",
            "separate_labels": self.labels_specified,
        }
        return data

    def write(self, filename: str = config.reg_file) -> str:
        """Writes the registration into disk
        Args:
            filename (str, optional): name of the file. Defaults to config.reg_file.
        """
        data = self.todict()
        filepath = os.path.join(self.out_path, filename)
        with open(filepath, "w") as f:
            yaml.dump(data, f)
