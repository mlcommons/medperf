import os
import yaml
import logging
from typing import List

from medperf import config
from medperf.comms import Comms
from medperf.utils import storage_path


class Benchmark:
    """
    Class representing a Benchmark

    a benchmark is a bundle of assets that enables quantitative 
    measurement of the performance of AI models for a specific 
    clinical problem. A Benchmark instance contains information
    regarding how to prepare datasets for execution, as well as
    what models to run and how to evaluate them.
    """

    def __init__(self, uid: str, benchmark_dict: dict):
        """Creates a new benchmark instance

        Args:
            uid (str): The benchmark UID
            benchmark_dict (dict): key-value representation of the benchmark.
        """
        self.uid = uid
        self.name = benchmark_dict["name"]
        self.description = benchmark_dict["description"]
        self.docs_url = benchmark_dict["docs_url"]
        self.created_at = benchmark_dict["created_at"]
        self.modified_at = benchmark_dict["modified_at"]
        self.owner = benchmark_dict["owner"]
        self.demo_dataset_url = benchmark_dict["demo_dataset_tarball_url"]
        self.demo_dataset_hash = benchmark_dict["demo_dataset_tarball_hash"]
        self.demo_dataset_generated_uid = benchmark_dict["demo_dataset_generated_uid"]
        self.data_preparation = benchmark_dict["data_preparation_mlcube"]
        self.reference_model = benchmark_dict["reference_model_mlcube"]
        self.models = benchmark_dict["models"]
        self.evaluator = benchmark_dict["data_evaluator_mlcube"]
        self.approval_status = benchmark_dict["approval_status"]

    @classmethod
    def get(
        cls, benchmark_uid: str, comms: Comms, force_update: bool = False
    ) -> "Benchmark":
        """Retrieves and creates a Benchmark instance from the server.
        If benchmark already exists in the platform then retrieve that
        version.

        Args:
            benchmark_uid (str): UID of the benchmark.
            comms (Comms): Instance of a communication interface.
            force_update (bool): Wether to download the benchmark regardless of cache. Defaults to False

        Returns:
            Benchmark: a Benchmark instance with the retrieved data.
        """
        # Get local benchmarks
        bmk_storage = storage_path(config.benchmarks_storage)
        local_bmks = os.listdir(bmk_storage)
        if str(benchmark_uid) in local_bmks and not force_update:
            benchmark_dict = cls.__get_local_dict(benchmark_uid)
        else:
            # Download benchmark
            benchmark_dict = comms.get_benchmark(benchmark_uid)
            ref_model = benchmark_dict["reference_model_mlcube"]
            add_models = cls.get_models_uids(benchmark_uid, comms)
            benchmark_dict["models"] = [ref_model] + add_models
        benchmark = cls(benchmark_uid, benchmark_dict)
        benchmark.write()
        return benchmark

    @classmethod
    def __get_local_dict(cls, benchmark_uid: str) -> dict:
        """Retrieves a local benchmark information

        Args:
            benchmark_uid (str): uid of the local benchmark

        Returns:
            dict: information of the benchmark
        """
        logging.info(f"Retrieving benchmark {benchmark_uid} from local storage")
        storage = storage_path(config.benchmarks_storage)
        bmk_storage = os.path.join(storage, str(benchmark_uid))
        bmk_file = os.path.join(bmk_storage, config.benchmarks_filename)
        with open(bmk_file, "r") as f:
            data = yaml.safe_load(f)

        return data

    @classmethod
    def get_models_uids(cls, benchmark_uid: str, comms: Comms) -> List[str]:
        """Retrieves the list of models associated to the benchmark

        Args:
            benchmark_uid (str): UID of the benchmark.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[str]: List of mlcube uids
        """
        return comms.get_benchmark_models(benchmark_uid)

    def todict(self) -> dict:
        """Dictionary representation of the benchmark instance

        Returns:
        dict: Dictionary containing benchmark information
        """
        return {
            "uid": self.uid,
            "name": self.name,
            "description": self.description,
            "docs_url": self.docs_url,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "owner": self.owner,
            "demo_dataset_tarball_url": self.demo_dataset_url,
            "demo_dataset_tarball_hash": self.demo_dataset_hash,
            "demo_dataset_generated_uid": self.demo_dataset_generated_uid,
            "data_preparation_mlcube": self.data_preparation,
            "reference_model_mlcube": self.reference_model,
            "models": self.models,
            "data_evaluator_mlcube": self.evaluator,
            "approval_status": self.approval_status,
        }

    def write(self, filename: str = config.benchmarks_filename) -> str:
        """Writes the benchmark into disk

        Args:
            filename (str, optional): name of the file. Defaults to config.benchmarks_filename.

        Returns:
            str: path to the created benchmark file
        """
        data = self.todict()
        storage = storage_path(config.benchmarks_storage)
        bmk_path = os.path.join(storage, str(self.uid))
        if not os.path.exists(bmk_path):
            os.mkdir(bmk_path)
        filepath = os.path.join(bmk_path, filename)
        with open(filepath, "w") as f:
            yaml.dump(data, f)
