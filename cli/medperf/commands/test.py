import logging
from time import time

from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset, Benchmark, Cube
from medperf.commands import BenchmarkExecution
from medperf.utils import pretty_error, init_storage


class TestExecution(BenchmarkExecution):
    @classmethod
    def run(
        cls,
        benchmark_uid: int,
        comms: Comms,
        ui: UI,
        data_uid: str = None,
        model_uid: int = None,
        cube_path: str = None,
        params_path: str = None,
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
            params_path (str, optional): Location of local mlcube parameters file.
                Must be provided if no dataset or model uid is provided.
        """
        # PSEUDOCODE
        # # ensures that the provided params are valid. if not it explains why
        # validate_params_combination()
        #
        # if data_uid is None:
        #   # Download demo dataset. Would be great if it was a dataset object on server
        #   # plus a download link (maybe on benchmark? maybe on dataset object itself?)
        #   # Returns a data_uid.
        #   data_uid = retrieve_demo_data()
        #
        # if model_uid is None:
        #   # Use reference model from benchmark
        #   model_uid = get_reference_model()
        # if cube_path is not None:
        #   # local unregistered cube should be built and used.
        #   # TODO: determine how to do this
        #   # My initial guess would be that this class should inherit from BenchmarkExecution
        #   # so that we can modify the relevant methods
        pass

    def __init__(
        self,
        benchmark_uid: int,
        data_uid: int,
        model_uid: int,
        comms: Comms,
        ui: UI,
        cube_path: str,
        params_path: str,
    ):
        super().__init__(benchmark_uid, data_uid, data_uid, model_uid, comms, ui)
        self.cube_path = cube_path
        self.params_path = params_path

    def prepare(self):
        init_storage()
        self.benchmark = Benchmark.get(self.benchmark_uid, self.comms)
        self.ui.print(f"Benchmark Execution: {self.benchmark.name}")
        if self.model_uid is None:
            self.model_uid = self.benchmark.reference_model
        if self.cube_path is not None:
            self.model_cube = Cube.get_local(self.cube_path, self.params_path)
        if self.data_uid is None:
            # Maybe we could add a get method to Dataset, that either
            # creates an instance with a local dataset or attempts to download
            # a dataset from the server
            self.data_uid = self.retrieve_demo_data()
        self.dataset = Dataset(self.data_uid, self.ui)

    def validate(self):
        data_provided = self.data_uid != self.benchmark.demo_data_uid
        local_model_provided = self.cube_path is not None
        model_provided = (
            self.model_uid != self.benchmark.reference_model
            and not local_model_provided
        )

        # We should only be testing one of the three possibilities
        variables_provided = sum([data_provided, model_provided, local_model_provided])

        if variables_provided > 1:
            pretty_error(
                "Too many testing parameters were set. Please only test one element at a time"
            )
        if variables_provided == 0:
            pretty_error("At least one testing element must be passed")

        super().validate()
