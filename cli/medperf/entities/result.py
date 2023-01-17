import os
import yaml
import logging
from typing import List, Union

from medperf.utils import storage_path
from medperf.entities.interface import Entity
from medperf.entities.models import ApprovableModel
from medperf.entities.dataset import Dataset
import medperf.config as config
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError


class Result(Entity, ApprovableModel):
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
        """Creates a new result instance

        Args:
            result_desc (Union[dict, ResultModel]): Result instance description
        """
        super().__init__(*args, **kwargs)

        dset = Dataset.get(self.dataset)
        self.generated_uid = f"b{self.benchmark}m{self.model}d{dset.generated_uid}"
        path = storage_path(config.results_storage)
        if self.id:
            path = os.path.join(path, str(self.id))
        else:
            path = os.path.join(path, self.generated_uid)

        self.path = path

    @classmethod
    def all(cls, local_only: bool = False, mine_only: bool = False) -> List["Result"]:
        """Gets and creates instances of all the user's results

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            mine_only (bool, optional): Wether to retrieve only current-user entities. Defaults to False.

        Returns:
            List[Result]: List containing all results
        """
        logging.info("Retrieving all results")
        results = []
        if not local_only:
            results = cls.__remote_all(mine_only=mine_only)

        remote_uids = set([result.id for result in results])

        local_results = cls.__local_all()

        results += [res for res in local_results if res.id not in remote_uids]

        return results

    @classmethod
    def __remote_all(cls, mine_only: bool = False) -> List["Result"]:
        results = []
        remote_func = config.comms.get_results
        if mine_only:
            remote_func = config.comms.get_user_results

        try:
            results_meta = remote_func()
            results = [cls(**meta) for meta in results_meta]
        except CommunicationRetrievalError:
            msg = "Couldn't retrieve all results from the server"
            logging.warning(msg)

        return results

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
    def get(cls, result_uid: str) -> "Result":
        """Retrieves and creates a Result instance obtained from the platform.
        If the result instance already exists in the user's machine, it loads
        the local instance

        Args:
            result_uid (str): UID /f the Result instance

        Returns:
            Result: Specified Result instance
        """
        logging.debug(f"Retrieving result {result_uid}")
        comms = config.comms
        # Try to download first
        try:
            result_dict = comms.get_result(result_uid)
        except CommunicationRetrievalError:
            # Get local results
            logging.warning(f"Getting result {result_uid} from comms failed")
            logging.info(f"Looking for result {result_uid} locally")
            result_dict = cls.__get_local_dict(result_uid)
        result = cls(**result_dict)
        result.write()
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
