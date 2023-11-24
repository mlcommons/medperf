import os
from medperf.exceptions import MedperfException
import yaml
import logging
from typing import List, Optional, Union
from pydantic import HttpUrl, Field, validator

import medperf.config as config
from medperf.entities.interface import Entity, Uploadable
from medperf.utils import storage_path
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError
from medperf.entities.schemas import MedperfSchema, ApprovableSchema, DeployableSchema
from medperf.account_management import get_medperf_user_data


class Benchmark(Entity, Uploadable, MedperfSchema, ApprovableSchema, DeployableSchema):
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
    demo_dataset_tarball_url: Optional[str]
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
    def all(cls, local_only: bool = False, filters: dict = {}) -> List["Benchmark"]:
        """Gets and creates instances of all retrievable benchmarks

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            filters (dict, optional): key-value pairs specifying filters to apply to the list of entities.

        Returns:
            List[Benchmark]: a list of Benchmark instances.
        """
        logging.info("Retrieving all benchmarks")
        benchmarks = []

        if not local_only:
            benchmarks = cls.__remote_all(filters=filters)

        remote_uids = set([bmk.id for bmk in benchmarks])

        local_benchmarks = cls.__local_all()

        benchmarks += [bmk for bmk in local_benchmarks if bmk.id not in remote_uids]

        return benchmarks

    @classmethod
    def __remote_all(cls, filters: dict) -> List["Benchmark"]:
        benchmarks = []
        try:
            comms_fn = cls.__remote_prefilter(filters)
            bmks_meta = comms_fn()
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
    def __remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_benchmarks
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_benchmarks
        return comms_fn

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
    def get(
        cls, benchmark_uid: Union[str, int], local_only: bool = False
    ) -> "Benchmark":
        """Retrieves and creates a Benchmark instance from the server.
        If benchmark already exists in the platform then retrieve that
        version.

        Args:
            benchmark_uid (str): UID of the benchmark.
            comms (Comms): Instance of a communication interface.

        Returns:
            Benchmark: a Benchmark instance with the retrieved data.
        """

        if not str(benchmark_uid).isdigit() or local_only:
            return cls.__local_get(benchmark_uid)

        try:
            return cls.__remote_get(benchmark_uid)
        except CommunicationRetrievalError:
            logging.warning(f"Getting Benchmark {benchmark_uid} from comms failed")
            logging.info(f"Looking for benchmark {benchmark_uid} locally")
            return cls.__local_get(benchmark_uid)

    @classmethod
    def __remote_get(cls, benchmark_uid: int) -> "Benchmark":
        """Retrieves and creates a Dataset instance from the comms instance.
        If the dataset is present in the user's machine then it retrieves it from there.

        Args:
            dset_uid (str): server UID of the dataset

        Returns:
            Dataset: Specified Dataset Instance
        """
        logging.debug(f"Retrieving benchmark {benchmark_uid} remotely")
        benchmark_dict = config.comms.get_benchmark(benchmark_uid)
        ref_model = benchmark_dict["reference_model_mlcube"]
        add_models = cls.get_models_uids(benchmark_uid)
        benchmark_dict["models"] = [ref_model] + add_models
        benchmark = cls(**benchmark_dict)
        benchmark.write()
        return benchmark

    @classmethod
    def __local_get(cls, benchmark_uid: Union[str, int]) -> "Benchmark":
        """Retrieves and creates a Dataset instance from the comms instance.
        If the dataset is present in the user's machine then it retrieves it from there.

        Args:
            dset_uid (str): server UID of the dataset

        Returns:
            Dataset: Specified Dataset Instance
        """
        logging.debug(f"Retrieving benchmark {benchmark_uid} locally")
        benchmark_dict = cls.__get_local_dict(benchmark_uid)
        benchmark = cls(**benchmark_dict)
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
    def get_models_uids(cls, benchmark_uid: int) -> List[int]:
        """Retrieves the list of models associated to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[int]: List of mlcube uids
        """
        associations = config.comms.get_benchmark_model_associations(benchmark_uid)
        models_uids = [
            assoc["model_mlcube"]
            for assoc in associations
            if assoc["approval_status"] == "APPROVED"
        ]
        return models_uids

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
        if self.for_test:
            raise InvalidArgumentError("Cannot upload test benchmarks.")
        body = self.todict()
        updated_body = config.comms.upload_benchmark(body)
        updated_body["models"] = body["models"]
        return updated_body

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Description": self.description,
            "Documentation": self.docs_url,
            "Created At": self.created_at,
            "Data Preparation MLCube": int(self.data_preparation_mlcube),
            "Reference Model MLCube": int(self.reference_model_mlcube),
            "Associated Models": ",".join(map(str, self.models)),
            "Data Evaluator MLCube": int(self.data_evaluator_mlcube),
            "State": self.state,
            "Approval Status": self.approval_status,
            "Registered": self.is_registered,
        }
