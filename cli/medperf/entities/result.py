import os
import yaml
import logging
from typing import List, Union

from medperf.utils import storage_path
from medperf.entities.interface import Entity, Uploadable
from medperf.entities.schemas import MedperfSchema, ApprovableSchema
import medperf.config as config
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError


class Result(Entity, Uploadable, MedperfSchema, ApprovableSchema):
    """
    Class representing a Result entry

    Results are obtained after successfully running a benchmark
    execution flow. They contain information regarding the
    components involved in obtaining metrics results, as well as the
    results themselves. This class provides methods for working with
    benchmark results and how to upload them to the backend.
    """

    benchmark: int
    model: int
    dataset: int
    results: dict
    metadata: dict = {}

    def __init__(self, *args, **kwargs):
        """Creates a new result instance"""
        super().__init__(*args, **kwargs)

        self.generated_uid = f"b{self.benchmark}m{self.model}d{self.dataset}"
        path = storage_path(config.results_storage)
        if self.id:
            path = os.path.join(path, str(self.id))
        else:
            path = os.path.join(path, self.generated_uid)

        self.path = path

    @classmethod
    def all(cls, local_only: bool = False, filters: dict = {}) -> List["Result"]:
        """Gets and creates instances of all the user's results

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            filters (dict, optional): key-value pairs specifying filters to apply to the list of entities.

        Returns:
            List[Result]: List containing all results
        """
        logging.info("Retrieving all results")
        results = []
        if not local_only:
            results = cls.__remote_all(filters=filters)

        remote_uids = set([result.id for result in results])

        local_results = cls.__local_all()

        results += [res for res in local_results if res.id not in remote_uids]

        return results

    @classmethod
    def __remote_all(cls, filters: dict) -> List["Result"]:
        results = []

        try:
            comms_fn = cls.__remote_prefilter(filters)
            results_meta = comms_fn()
            results = [cls(**meta) for meta in results_meta]
        except CommunicationRetrievalError:
            msg = "Couldn't retrieve all results from the server"
            logging.warning(msg)

        return results

    @classmethod
    def __remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_results
        if "owner" in filters and filters["owner"] == config.current_user["id"]:
            comms_fn = config.comms.get_user_results
        if "benchmark" in filters:
            bmk = filters["benchmark"]

            def get_benchmark_results():
                # Decorate the benchmark results remote function so it has the same signature
                # as all the comms_fns
                return config.comms.get_benchmark_results(bmk)

            comms_fn = get_benchmark_results

        return comms_fn

    @classmethod
    def __local_all(cls) -> List["Result"]:
        results = []
        results_storage = storage_path(config.results_storage)
        try:
            uids = next(os.walk(results_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over the dataset directory"
            logging.warning(msg)
            raise RuntimeError(msg)

        for uid in uids:
            local_meta = cls.__get_local_dict(uid)
            result = cls(**local_meta)
            results.append(result)

        return results

    @classmethod
    def get(cls, result_uid: Union[str, int], local_only: bool = False) -> "Result":
        """Retrieves and creates a Result instance obtained from the platform.
        If the result instance already exists in the user's machine, it loads
        the local instance

        Args:
            result_uid (str): UID of the Result instance

        Returns:
            Result: Specified Result instance
        """
        if not str(result_uid).isdigit() or local_only:
            return cls.__local_get(result_uid)

        try:
            return cls.__remote_get(result_uid)
        except CommunicationRetrievalError:
            logging.warning(f"Getting Result {result_uid} from comms failed")
            logging.info(f"Looking for result {result_uid} locally")
            return cls.__local_get(result_uid)

    @classmethod
    def __remote_get(cls, result_uid: int) -> "Result":
        """Retrieves and creates a Dataset instance from the comms instance.
        If the dataset is present in the user's machine then it retrieves it from there.

        Args:
            result_uid (str): server UID of the dataset

        Returns:
            Dataset: Specified Dataset Instance
        """
        logging.debug(f"Retrieving result {result_uid} remotely")
        meta = config.comms.get_result(result_uid)
        result = cls(**meta)
        result.write()
        return result

    @classmethod
    def __local_get(cls, result_uid: Union[str, int]) -> "Result":
        """Retrieves and creates a Dataset instance from the comms instance.
        If the dataset is present in the user's machine then it retrieves it from there.

        Args:
            result_uid (str): server UID of the dataset

        Returns:
            Dataset: Specified Dataset Instance
        """
        logging.debug(f"Retrieving result {result_uid} locally")
        local_meta = cls.__get_local_dict(result_uid)
        result = cls(**local_meta)
        return result

    def todict(self):
        return self.extended_dict()

    def upload(self):
        """Uploads the results to the comms

        Args:
            comms (Comms): Instance of the communications interface.
        """
        results_info = self.todict()
        updated_results_info = config.comms.upload_result(results_info)
        return updated_results_info

    def write(self):
        result_file = os.path.join(self.path, config.results_info_file)
        if os.path.exists(result_file):
            write_access = os.access(result_file, os.W_OK)
            logging.debug(f"file has write access? {write_access}")
            if not write_access:
                logging.debug("removing outdated and inaccessible results")
                os.remove(result_file)
        os.makedirs(self.path, exist_ok=True)
        with open(result_file, "w") as f:
            yaml.dump(self.todict(), f)
        return result_file

    @classmethod
    def __get_local_dict(cls, local_uid):
        result_path = os.path.join(storage_path(config.results_storage), str(local_uid))
        result_file = os.path.join(result_path, config.results_info_file)
        if not os.path.exists(result_file):
            raise InvalidArgumentError(
                f"The requested result {local_uid} could not be retrieved"
            )
        with open(result_file, "r") as f:
            results_info = yaml.safe_load(f)
        return results_info

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Benchmark": self.benchmark,
            "Model": self.model,
            "Dataset": self.dataset,
            "Partial": self.metadata["partial"],
            "Approval Status": self.approval_status,
            "Created At": self.created_at,
            "Registered": self.is_registered,
        }
