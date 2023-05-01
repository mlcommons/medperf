import logging
import os
from pathlib import Path
from medperf.entities.dataset import Dataset
from medperf.enums import Status
import medperf.config as config
from medperf.entities.cube import Cube
from medperf.entities.benchmark import Benchmark
from medperf.utils import (
    check_cube_validity,
    remove_path,
    generate_tmp_path,
    get_folder_sha1,
    storage_path,
)
from medperf.exceptions import InvalidArgumentError
import yaml


class DataPreparation:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        prep_cube_uid: int,
        data_path: str,
        labels_path: str,
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
            run_test,
        )
        preparation.validate()
        with preparation.ui.interactive():
            preparation.get_prep_cube()
            preparation.run_cube_tasks()
        preparation.get_statistics()
        preparation.generate_uids()
        preparation.to_permanent_path()
        preparation.write()
        return preparation.generated_uid

    def __init__(
        self,
        benchmark_uid: int,
        prep_cube_uid: int,
        data_path: str,
        labels_path: str,
        name: str,
        description: str,
        location: str,
        run_test=False,
    ):
        self.comms = config.comms
        self.ui = config.ui
        self.data_path = str(Path(data_path).resolve())
        self.labels_path = str(Path(labels_path).resolve())
        out_path = generate_tmp_path()
        self.out_statistics_path = generate_tmp_path()
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
        logging.debug(f"tmp data preparation output: {out_path}")
        logging.debug(f"tmp data statistics output: {self.out_statistics_path}")

    def validate(self):
        if not os.path.exists(self.data_path):
            raise InvalidArgumentError("The provided data path doesn't exist")
        if not os.path.exists(self.labels_path):
            raise InvalidArgumentError("The provided labels path doesn't exist")

        too_many_resources = self.benchmark_uid and self.prep_cube_uid
        no_resource = self.benchmark_uid is None and self.prep_cube_uid is None
        if no_resource or too_many_resources:
            raise InvalidArgumentError(
                "Must provide either a benchmark or a preparation mlcube"
            )

    def get_prep_cube(self):
        cube_uid = self.prep_cube_uid
        if cube_uid is None:
            benchmark = Benchmark.get(self.benchmark_uid)
            cube_uid = benchmark.data_preparation_mlcube
            self.ui.print(f"Benchmark Data Preparation: {benchmark.name}")
        self.ui.text = f"Retrieving data preparation cube: '{cube_uid}'"
        self.cube = Cube.get(cube_uid)
        self.ui.print("> Preparation cube download complete")
        check_cube_validity(self.cube)

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
        prepare_str_params = {
            "Ptasks.prepare.parameters.input.data_path.opts": "ro",
            "Ptasks.prepare.parameters.input.labels_path.opts": "ro",
        }

        sanity_params = {
            "data_path": out_datapath,
        }
        sanity_str_params = {
            "Ptasks.sanity_check.parameters.input.data_path.opts": "ro"
        }

        statistics_params = {
            "data_path": out_datapath,
            "output_path": self.out_statistics_path,
        }
        statistics_str_params = {
            "Ptasks.statistics.parameters.input.data_path.opts": "ro"
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
            task="prepare",
            string_params=prepare_str_params,
            timeout=prepare_timeout,
            **prepare_params,
        )
        self.ui.print("> Cube execution complete")

        self.ui.text = "Running sanity check..."
        self.cube.run(
            task="sanity_check",
            string_params=sanity_str_params,
            timeout=sanity_check_timeout,
            **sanity_params,
        )
        self.ui.print("> Sanity checks complete")

        self.ui.text = "Generating statistics..."
        self.cube.run(
            task="statistics",
            string_params=statistics_str_params,
            timeout=statistics_timeout,
            **statistics_params,
        )
        self.ui.print("> Statistics complete")

    def get_statistics(self):
        with open(self.out_statistics_path, "r") as f:
            stats = yaml.safe_load(f)
        self.generated_metadata = stats

    def generate_uids(self):
        """Auto-generates dataset UIDs for both input and output paths"""
        self.in_uid = get_folder_sha1(self.data_path)
        self.generated_uid = get_folder_sha1(self.out_datapath)

    def to_permanent_path(self) -> str:
        """Renames the temporary data folder to permanent one using the hash of
        the registration file
        """
        new_path = os.path.join(storage_path(config.data_storage), self.generated_uid)
        remove_path(new_path)
        os.rename(self.out_path, new_path)
        self.out_path = new_path

    def todict(self) -> dict:
        """Dictionary representation of the dataset

        Returns:
            dict: dictionary containing information pertaining the dataset.
        """
        return {
            "id": None,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "data_preparation_mlcube": self.cube.identifier,
            "input_data_hash": self.in_uid,
            "generated_uid": self.generated_uid,
            "split_seed": 0,  # Currently this is not used
            "generated_metadata": self.generated_metadata,
            "status": Status.PENDING.value,  # not in the server
            "state": "OPERATION",
            "separate_labels": self.labels_specified,  # not in the server
            "for_test": self.run_test,  # not in the server (OK)
        }

    def write(self) -> str:
        """Writes the registration into disk
        Args:
            filename (str, optional): name of the file. Defaults to config.reg_file.
        """
        dataset_dict = self.todict()
        dataset = Dataset(**dataset_dict)
        dataset.write()
