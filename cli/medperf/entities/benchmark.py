import os
import yaml
import logging
from typing import List

import medperf.config as config
from medperf.comms.comms import Comms
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
        # Getting None by default allows creating empty benchmarks for tests
        self.name = benchmark_dict.get("name", None)
        self.description = benchmark_dict.get("description", None)
        self.docs_url = benchmark_dict.get("docs_url", None)
        self.created_at = benchmark_dict.get("created_at", None)
        self.modified_at = benchmark_dict.get("modified_at", None)
        self.owner = benchmark_dict.get("owner", None)
        self.demo_dataset_url = benchmark_dict.get("demo_dataset_tarball_url", None)
        self.demo_dataset_hash = benchmark_dict.get("demo_dataset_tarball_hash", None)
        self.demo_dataset_generated_uid = benchmark_dict.get(
            "demo_dataset_generated_uid", None
        )
        self.data_preparation = benchmark_dict.get("data_preparation_mlcube", None)
        self.reference_model = benchmark_dict.get("reference_model_mlcube", None)
        self.models = benchmark_dict.get("models", None)
        self.evaluator = benchmark_dict.get("data_evaluator_mlcube", None)
        self.approval_status = benchmark_dict.get("approval_status", None)

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
    def tmp(
        cls,
        data_preparator: str,
        model: str,
        evaluator: str,
        demo_url: str = None,
        demo_hash: str = None,
    ) -> "Benchmark":
        """Creates a temporary instance of the benchmark

        Args:
            data_preparator (str): UID of the data preparator cube to use.
            model (str): UID of the model cube to use.
            evaluator (str): UID of the evaluator cube to use.
            demo_url (str, optional): URL to obtain the demo dataset. Defaults to None.
            demo_hash (str, optional): Hash of the demo dataset tarball file. Defaults to None.

        Returns:
            Benchmark: a benchmark instance
        """
        benchmark_uid = f"{config.tmp_prefix}{data_preparator}_{model}_{evaluator}"
        benchmark_dict = {
            "name": benchmark_uid,
            "data_preparation_mlcube": data_preparator,
            "reference_model_mlcube": model,
            "data_evaluator_mlcube": evaluator,
            "demo_dataset_tarball_url": demo_url,
            "demo_dataset_tarball_hash": demo_hash,
            "models": [model],
        }
        benchmark = Benchmark(benchmark_uid, benchmark_dict)
        benchmark.write()
        return benchmark

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
        return filepath
