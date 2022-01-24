import os
import logging
from time import time
from medperf.commands.prepare import DataPreparation

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset, Benchmark, Cube, benchmark
from medperf.commands import BenchmarkExecution
from medperf.utils import pretty_error, get_uids
from medperf.config import config


class TestExecution:
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        comms: Comms,
        ui: UI,
        data_uid: str = None,
        model_uid: int = None,
        cube_path: str = None,
    ):
        """Execute a test workflow for a specific benchmark

        Args:
            benchmark_uid (int): Benchmark to run the test workflow for
            data_uid (str, optional): registered dataset uid. 
                If none provided, it defaults to benchmark test dataset.
            model_uid (int, optional): model mlcube uid. 
                If none provided, it defaults to benchmark reference model.
            cube_path (str, optional): Location of local model mlcube. Must be
                provided if no dataset or model uid is provided.
        """
        test_exec = cls(benchmark_uid, data_uid, model_uid, comms, ui, cube_path)
        test_exec.validate()
        test_exec.set_model_uid()
        test_exec.set_data_uid()
        test_exec.execute_benchmark()
        return test_exec.benchmark_uid, test_exec.data_uid, test_exec.model_uid

    def __init__(
        self,
        benchmark_uid: int,
        data_uid: int,
        model_uid: int,
        comms: Comms,
        ui: UI,
        cube_path: str,
    ):
        self.benchmark_uid = benchmark_uid
        self.data_uid = data_uid
        self.model_uid = model_uid
        self.comms = comms
        self.ui = ui
        self.cube_path = cube_path
        self.benchmark = Benchmark.get(benchmark_uid, comms)

    def set_model_uid(self):
        """Assigns the model_uid used for testing according to the initialization parameters.
        If a cube_path is provided, it will create a temporary uid and link the cube path to
        the medperf storage path.
        """
        if self.model_uid is None:
            self.model_uid = self.benchmark.reference_model

        if self.cube_path:
            self.model_uid = config["test_cube_prefix"] + str(int(time()))
            dst = os.path.join(config["cubes_storage"], self.model_uid)
            os.symlink(self.cube_path, dst)

    def set_data_uid(self):
        """Assigns the data_uid used for testing according to the initialization parameters.
        If no data_uid is provided, it will retrieve the demo data and execute the data 
        preparation flow.
        """
        if self.data_uid is None:
            data_path, labels_path = self.download_demo_data()
            self.data_uid = DataPreparation.run(
                self.benchmark_uid,
                data_path,
                labels_path,
                self.comms,
                self.ui,
                run_test=True,
            )
            # Dataset will not be registered, so we must mock its uid
            dset = Dataset(self.data_uid, self.ui)
            dset.uid = self.data_uid
            dset.set_registration()

    def execute_benchmark(self):
        """Runs the benchmark execution flow given the specified testing parameters
        """
        BenchmarkExecution.run(
            self.benchmark_uid,
            self.data_uid,
            self.model_uid,
            self.comms,
            self.ui,
            run_test=True,
        )

    def download_demo_data(self):
        """Retrieves the demo dataset associated to the specified benchmark

        Returns:
            data_path (str): Location of the downloaded data
            labels_path (str): Location of the downloaded labels
        """
        # TODO: implement this
        return (
            "/Users/aristizabal-factored/Documents/mlcommons_p0/local_workspace/CheXpert-v1.0-small",
            "/Users/aristizabal-factored/Documents/mlcommons_p0/local_workspace/CheXpert-v1.0-small/valid.csv",
        )

    def validate(self):
        # TODO Remove fallback
        self.benchmark.demo_data_uid = "test"
        data_provided = False and self.data_uid != self.benchmark.demo_data_uid
        local_model_provided = self.cube_path is not None
        model_provided = (
            self.model_uid != self.benchmark.reference_model
            and not local_model_provided
        )

        # We should only be testing one of the three possibilities
        variables_provided = sum([data_provided, model_provided, local_model_provided])

        if variables_provided > 1:
            pretty_error(
                "Too many testing parameters were set. Please only test one element at a time",
                self.ui,
            )
        if variables_provided == 0:
            pretty_error("At least one testing element must be passed", self.ui)

        # Ensure the cube_path is a directory pointing to an mlcube
        cube_path_specified = self.cube_path is not None
        if cube_path_specified:
            cube_path_isdir = os.path.isdir(self.cube_path)
            manifest_file = os.path.join(self.cube_path, config["cube_filename"])
            cube_path_contains_manifest_file = os.path.exists(manifest_file)
            valid_cube_path = cube_path_isdir and cube_path_contains_manifest_file
            if not valid_cube_path:
                pretty_error(
                    "The specified cube_path is invalid. Must point to a directory containing an mlcube.yaml manifest file",
                    self.ui,
                )
