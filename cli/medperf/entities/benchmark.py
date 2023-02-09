import os
from medperf.exceptions import MedperfException
import yaml
import logging
from typing import List, Optional, Union
from pydantic import HttpUrl, Field, validator

import medperf.config as config
from medperf.entities.interface import Entity
from medperf.utils import storage_path
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError
from medperf.entities.schemas import MedperfSchema, ApprovableSchema, DeployableSchema


class Benchmark(Entity, MedperfSchema, ApprovableSchema, DeployableSchema):
    """
    Class representing a Benchmark

    a benchmark is a bundle of assets that enables quantitative
    measurement of the performance of AI models for a specific
    clinical problem. A Benchmark instance contains information
    regarding how to prepare datasets for execution, as well as
    what models to run and how to evaluate them.
    """

    description: Optional[str] = Field(None, max_length=20)
    docs_url: Optional[HttpUrl]
    demo_dataset_tarball_url: Optional[HttpUrl]
    demo_dataset_tarball_hash: Optional[str]
    demo_dataset_generated_uid: Optional[str]
    data_preparation_mlcube: int
    reference_model_mlcube: int
    data_evaluator_mlcube: int
    models: List[int] = None
    metadata: dict = {}
    user_metadata: dict = {}
    is_active: bool = True

    @validator("models", pre=True, always=True)
    def set_default_models_value(cls, value, values, **kwargs):
        if not value:
            # Empty or None value assigned
            return [values["reference_model_mlcube"]]
        return value

    def __init__(self, *args, **kwargs):
        """Creates a new benchmark instance

        Args:
            bmk_desc (Union[dict, BenchmarkModel]): Benchmark instance description
        """
        super().__init__(*args, **kwargs)

        self.generated_uid = f"p{self.data_preparation_mlcube}m{self.reference_model_mlcube}e{self.data_evaluator_mlcube}"
        path = storage_path(config.benchmarks_storage)
        if self.id:
            path = os.path.join(path, str(self.id))
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

        remote_uids = set([bmk.id for bmk in benchmarks])

        local_benchmarks = cls.__local_all()

        benchmarks += [bmk for bmk in local_benchmarks if bmk.id not in remote_uids]

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
            benchmarks = [cls(**meta) for meta in bmks_meta]
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
            raise MedperfException(msg)

        for uid in uids:
            meta = cls.__get_local_dict(uid)
            benchmark = cls(**meta)
            benchmarks.append(benchmark)

        return benchmarks

    @classmethod
    def get(cls, benchmark_uid: Union[str, int]) -> "Benchmark":
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
        benchmark = cls(**benchmark_dict)
        benchmark.write()
        return benchmark

    @classmethod
    def __get_local_dict(cls, benchmark_uid) -> dict:
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
        data_preparator: int,
        model: int,
        evaluator: int,
        demo_url: str = None,
        demo_hash: str = None,
    ) -> "Benchmark":
        """Creates a temporary instance of the benchmark

        Args:
            data_preparator (int): UID of the data preparator cube to use.
            model (int): UID of the model cube to use.
            evaluator (int): UID of the evaluator cube to use.
            demo_url (str, optional): URL to obtain the demo dataset. Defaults to None.
            demo_hash (str, optional): Hash of the demo dataset tarball file. Defaults to None.

        Returns:
            Benchmark: a benchmark instance
        """
        name = f"b{data_preparator}m{model}e{evaluator}"
        benchmark_dict = {
            "id": None,
            "name": name,
            "data_preparation_mlcube": data_preparator,
            "reference_model_mlcube": model,
            "data_evaluator_mlcube": evaluator,
            "demo_dataset_tarball_url": demo_url,
            "demo_dataset_tarball_hash": demo_hash,
            "models": [model],  # not in the server (OK)
        }
        benchmark = cls(**benchmark_dict)
        benchmark.write()
        return benchmark

    @classmethod
    def get_models_uids(cls, benchmark_uid: int) -> List[int]:
        """Retrieves the list of models associated to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[int]: List of mlcube uids
        """
        return config.comms.get_benchmark_models(benchmark_uid)

    def todict(self) -> dict:
        """Dictionary representation of the benchmark instance

        Returns:
        dict: Dictionary containing benchmark information
        """
        return self.extended_dict()

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
