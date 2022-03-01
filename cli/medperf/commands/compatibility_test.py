import os
import yaml
import logging
from time import time
from medperf.commands.dataset import DataPreparation

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset, Benchmark
from medperf.commands.result import BenchmarkExecution
from medperf.utils import pretty_error, untar, get_file_sha1
from medperf import config


class CompatibilityTestExecution:
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
        logging.info("Starting test execution")
        test_exec = cls(benchmark_uid, data_uid, model_uid, cube_path, comms, ui)
        # test_exec.validate()
        test_exec.set_model_uid()
        test_exec.set_data_uid()
        test_exec.execute_benchmark()
        return test_exec.benchmark_uid, test_exec.data_uid, test_exec.model_uid

    def __init__(
        self,
        benchmark_uid: int,
        data_uid: int,
        model_uid: int,
        cube_path: str,
        comms: Comms,
        ui: UI,
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
        logging.info("Establishing model_uid for test execution")
        if self.model_uid is None:
            logging.info("model_uid not provided. Using reference cube")
            self.model_uid = self.benchmark.reference_model

        if self.cube_path:
            logging.info("local cube path provided. Creating symbolic link")
            self.model_uid = config.test_cube_prefix + str(int(time()))
            dst = os.path.join(config.cubes_storage, self.model_uid)
            os.symlink(self.cube_path, dst)
            logging.info(f"local cube will linked to path: {dst}")

    def set_data_uid(self):
        """Assigns the data_uid used for testing according to the initialization parameters.
        If no data_uid is provided, it will retrieve the demo data and execute the data 
        preparation flow.
        """
        logging.info("Establishing data_uid for test execution")
        if self.data_uid is None:
            logging.info("Data uid not provided. Using benchmark demo dataset")
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
            logging.info("Defining local data uid")
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
        demo_data_url = self.benchmark.demo_dataset_url
        file_path = self.comms.get_benchmark_demo_dataset(demo_data_url)

        # Check demo dataset integrity
        file_hash = get_file_sha1(file_path)
        if file_hash != self.benchmark.demo_dataset_hash:
            pretty_error("Demo dataset hash doesn't match expected hash", self.ui)

        untar_path = untar(file_path, remove=False)

        # It is assumed that all demo datasets contain a file
        # which specifies the input of the data preparation step
        paths_file = os.path.join(untar_path, config.demo_dset_paths_file)
        with open(paths_file, "r") as f:
            paths = yaml.safe_load(f)

        data_path = os.path.join(untar_path, paths["data_path"])
        labels_path = os.path.join(untar_path, paths["labels_path"])
        return data_path, labels_path

    def validate(self):
        logging.info("Validating test execution")
        demo_data_uid = self.benchmark.demo_dataset_generated_uid
        data_provided = self.data_uid != demo_data_uid

        logging.debug(f"Data_uid provided? {data_provided}")
        local_model_provided = self.cube_path is not None
        logging.debug(f"Local cube provided? {data_provided}")
        model_provided = (
            self.model_uid is not None
            and self.model_uid != self.benchmark.reference_model
        )
        logging.debug(f"Model provided? {model_provided}")

        # We should only be testing one of the three possibilities
        variables_provided = sum([data_provided, model_provided, local_model_provided])
        logging.debug(f"Number of testing values provided: {variables_provided}")

        if variables_provided > 1:
            pretty_error(
                "Too many testing parameters were set. Please only test one element at a time",
                self.ui,
            )
        if variables_provided == 0:
            pretty_error("At least one testing element must be passed", self.ui)

        # Ensure the cube_path is a directory pointing to an mlcube
        if local_model_provided:
            logging.info("Ensuring local cube is valid")
            cube_path_isdir = os.path.isdir(self.cube_path)
            manifest_file = os.path.join(self.cube_path, config.cube_filename)
            cube_path_contains_manifest_file = os.path.exists(manifest_file)
            valid_cube_path = cube_path_isdir and cube_path_contains_manifest_file
            if not valid_cube_path:
                pretty_error(
                    "The specified cube_path is invalid. Must point to a directory containing an mlcube.yaml manifest file",
                    self.ui,
                )
