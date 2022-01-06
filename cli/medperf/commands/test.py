from medperf.ui import UI
from medperf.comms import Comms
from medperf.entities import Dataset
from medperf.commands import BenchmarkExecution
from medperf.utils import pretty_error


class Test:
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
