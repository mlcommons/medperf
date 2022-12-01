import os
from medperf.enums import Status
import yaml
import logging
from typing import List

import medperf.config as config
from medperf.entities.interface import Entity
from medperf.utils import storage_path
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError


class Benchmark(Entity):
    """
    Class representing a Benchmark

    a benchmark is a bundle of assets that enables quantitative
    measurement of the performance of AI models for a specific
    clinical problem. A Benchmark instance contains information
    regarding how to prepare datasets for execution, as well as
    what models to run and how to evaluate them.
    """

    def __init__(self, bmk_dict: dict):
        """Creates a new benchmark instance

        Args:
            uid (str): The benchmark UID
            benchmark_dict (dict): key-value representation of the benchmark.
        """
        self.uid = bmk_dict["id"]
        self.name = bmk_dict["name"]
        self.description = bmk_dict["description"]
        self.docs_url = bmk_dict["docs_url"]
        self.created_at = bmk_dict["created_at"]
        self.modified_at = bmk_dict["modified_at"]
        self.approved_at = bmk_dict["approved_at"]
        self.owner = bmk_dict["owner"]
        self.demo_dataset_url = bmk_dict["demo_dataset_tarball_url"]
        self.demo_dataset_hash = bmk_dict["demo_dataset_tarball_hash"]
        self.demo_dataset_generated_uid = bmk_dict["demo_dataset_generated_uid"]
        self.data_preparation = bmk_dict["data_preparation_mlcube"]
        self.reference_model = bmk_dict["reference_model_mlcube"]
        self.evaluator = bmk_dict["data_evaluator_mlcube"]
        self.models = bmk_dict["models"]
        self.state = bmk_dict["state"]
        self.is_valid = bmk_dict["is_valid"]
        self.is_active = bmk_dict["is_active"]
        self.approval_status = Status(bmk_dict["approval_status"])
        self.metadata = bmk_dict["metadata"]
        self.user_metadata = bmk_dict["user_metadata"]

        self.generated_uid = (
            f"{self.data_preparation}_{self.reference_model}_{self.evaluator}"
        )
        path = storage_path(config.benchmarks_storage)
        if self.uid:
            path = os.path.join(path, str(self.uid))
        else:
            path = os.path.join(path, self.generated_uid)
        self.path = path

    @classmethod
    def all(
        cls, local_only: bool = False, mine_only: bool = False
    ) -> List["Benchmark"]:
        """Gets and creates instances of all retrievable benchmarks

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            mine_only (bool, optional): Wether to retrieve only current-user entities. Defaults to False.

        Returns:
            List[Benchmark]: a list of Benchmark instances.
        """
        logging.info("Retrieving all benchmarks")
        benchmarks = []

        if not local_only:
            benchmarks = cls.__remote_all(mine_only=mine_only)

        remote_uids = set([bmk.uid for bmk in benchmarks])

        local_benchmarks = cls.__local_all()

        benchmarks += [bmk for bmk in local_benchmarks if bmk.uid not in remote_uids]

        return benchmarks

    @classmethod
    def __remote_all(cls, mine_only: bool = False) -> List["Benchmark"]:
        benchmarks = []
        remote_func = config.comms.get_benchmarks
        if mine_only:
            remote_func = config.comms.get_user_benchmarks

        try:
            bmks_meta = remote_func()
            for bmk_meta in bmks_meta:
                # Loading all related models for all benchmarks could be expensive.
                # Most probably not necessary when getting all benchmarks.
                # If associated models for a benchmark are needed then use Benchmark.get()
                bmk_meta["models"] = [bmk_meta["reference_model_mlcube"]]
            benchmarks = [cls(meta) for meta in bmks_meta]
        except CommunicationRetrievalError:
            msg = "Couldn't retrieve all benchmarks from the server"
            logging.warning(msg)

        return benchmarks

    @classmethod
    def __local_all(cls) -> List["Benchmark"]:
        benchmarks = []
        bmks_storage = storage_path(config.benchmarks_storage)
        try:
            uids = next(os.walk(bmks_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over benchmarks directory"
            logging.warning(msg)
            raise RuntimeError(msg)

        for uid in uids:
            meta = cls.__get_local_dict(uid)
            benchmark = cls(meta)
            benchmarks.append(benchmark)

        return benchmarks

    @classmethod
    def get(cls, benchmark_uid: str) -> "Benchmark":
        """Retrieves and creates a Benchmark instance from the server.
        If benchmark already exists in the platform then retrieve that
        version.

        Args:
            benchmark_uid (str): UID of the benchmark.
            comms (Comms): Instance of a communication interface.

        Returns:
            Benchmark: a Benchmark instance with the retrieved data.
        """
        comms = config.comms
        # Try to download first
        try:
            benchmark_dict = comms.get_benchmark(benchmark_uid)
            ref_model = benchmark_dict["reference_model_mlcube"]
            add_models = cls.get_models_uids(benchmark_uid)
            benchmark_dict["models"] = [ref_model] + add_models
        except CommunicationRetrievalError:
            # Get local benchmarks
            logging.warning(f"Getting benchmark {benchmark_uid} from comms failed")
            logging.info(f"Looking for benchmark {benchmark_uid} locally")
            benchmark_dict = cls.__get_local_dict(benchmark_uid)
        benchmark = cls(benchmark_dict)
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
        if not os.path.exists(bmk_file):
            raise InvalidArgumentError("No benchmark with the given uid could be found")
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
        name = f"{data_preparator}_{model}_{evaluator}"
        benchmark_dict = {
            "id": None,
            "name": name,
            "data_preparation_mlcube": data_preparator,
            "reference_model_mlcube": model,
            "data_evaluator_mlcube": evaluator,
            "demo_dataset_tarball_url": demo_url,
            "demo_dataset_tarball_hash": demo_hash,
            "models": [model],  # not in the server (OK)
            "description": None,
            "docs_url": None,
            "created_at": None,
            "modified_at": None,
            "approved_at": None,
            "owner": None,
            "demo_dataset_generated_uid": None,
            "state": "DEVELOPMENT",
            "is_valid": True,
            "is_active": True,
            "approval_status": Status.PENDING.value,
            "metadata": {},
            "user_metadata": {},
        }
        benchmark = cls(benchmark_dict)
        benchmark.write()
        return benchmark

    @classmethod
    def get_models_uids(cls, benchmark_uid: str) -> List[str]:
        """Retrieves the list of models associated to the benchmark

        Args:
            benchmark_uid (str): UID of the benchmark.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[str]: List of mlcube uids
        """
        return config.comms.get_benchmark_models(benchmark_uid)

    def todict(self) -> dict:
        """Dictionary representation of the benchmark instance

        Returns:
        dict: Dictionary containing benchmark information
        """
        return {
            "id": self.uid,
            "name": self.name,
            "description": self.description,
            "docs_url": self.docs_url,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "approved_at": self.approved_at,
            "owner": self.owner,
            "demo_dataset_tarball_url": self.demo_dataset_url,
            "demo_dataset_tarball_hash": self.demo_dataset_hash,
            "demo_dataset_generated_uid": self.demo_dataset_generated_uid,
            "data_preparation_mlcube": int(self.data_preparation),
            "reference_model_mlcube": int(self.reference_model),
            "models": self.models,  # not in the server (OK)
            "data_evaluator_mlcube": int(self.evaluator),
            "state": self.state,
            "is_valid": self.is_valid,
            "is_active": self.is_active,
            "approval_status": self.approval_status.value,
            "metadata": self.metadata,
            "user_metadata": self.user_metadata,
        }

    def write(self) -> str:
        """Writes the benchmark into disk

        Args:
            filename (str, optional): name of the file. Defaults to config.benchmarks_filename.

        Returns:
            str: path to the created benchmark file
        """
        data = self.todict()
        bmk_file = os.path.join(self.path, config.benchmarks_filename)
        if not os.path.exists(bmk_file):
            os.makedirs(self.path, exist_ok=True)
        with open(bmk_file, "w") as f:
            yaml.dump(data, f)
        return bmk_file

    def upload(self):
        """Uploads a benchmark to the server

        Args:
            comms (Comms): communications entity to submit through
        """
        body = self.todict()
        updated_body = config.comms.upload_benchmark(body)
        updated_body["models"] = body["models"]
        return updated_body
