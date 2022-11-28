import os
from pathlib import Path
from medperf.enums import Status
import yaml
import logging
from typing import List
from shutil import rmtree

from medperf.utils import storage_path
from medperf.entities.interface import Entity
import medperf.config as config
from medperf.exceptions import CommunicationRetrievalError, InvalidArgumentError


class Result(Entity):
    """
    Class representing a Result entry

    Results are obtained after successfully running a benchmark
    execution flow. They contain information regarding the
    components involved in obtaining metrics results, as well as the
    results themselves. This class provides methods for working with
    benchmark results and how to upload them to the backend.
    """

    def __init__(self, results_info: dict):
        """Creates a new result instance

        Args:
            benchmark_uid (str): UID of the executed benchmark.
            dataset_uid (str): UID of the dataset used.
            model_uid (str): UID of the model used.
            results()
        """
        self.uid = results_info["id"]
        self.name = results_info["name"]
        self.owner = results_info["owner"]
        self.benchmark_uid = results_info["benchmark"]
        self.model_uid = results_info["model"]
        self.dataset_uid = results_info["dataset"]
        self.results = results_info["results"]
        self.status = Status(results_info["approval_status"])
        self.metadata = results_info["metadata"]
        self.approved_at = results_info["approved_at"]
        self.created_at = results_info["created_at"]
        self.modified_at = results_info["modified_at"]

        self.tmp_uid = f"{self.benchmark_uid}_{self.model_uid}_{self.dataset_uid}"
        path = storage_path(config.results_storage)
        tmp_path = os.path.join(path, self.tmp_uid)
        if not self.uid:
            self.uid = self.tmp_uid
        path = os.path.join(path, str(self.uid))

        self.tmp_path = os.path.join(tmp_path, config.results_info_file)
        self.path = os.path.join(path, config.results_info_file)

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
        remote_func = config.comms.get_results
        if mine_only:
            remote_func = config.comms.get_user_results

        if not local_only:
            try:
                results_meta = remote_func()
                results = [cls(meta) for meta in results_meta]
            except CommunicationRetrievalError:
                msg = "Couldn't retrieve all results from the server"
                logging.warning(msg)

        remote_uids = set([str(result.uid) for result in results])

        results_storage = storage_path(config.results_storage)
        try:
            uids = next(os.walk(results_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over the dataset directory"
            logging.warning(msg)
            raise RuntimeError(msg)

        for uid in uids:
            if uid in remote_uids:
                continue
            local_meta = cls.__get_local_dict(uid)
            result = cls(local_meta)
            results.append(result)

        return results

    @classmethod
    def get(cls, result_uid: str) -> "Result":
        """Retrieves and creates a Result instance obtained from the platform.
        If the result instance already exists in the user's machine, it loads
        the local instance

        Args:
            result_uid (str): UID of the Result instance

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
        result = cls(result_dict)
        result.write()
        return result

    def todict(self):
        return {
            "id": self.uid,
            "name": self.name,
            "owner": self.owner,
            "benchmark": self.benchmark_uid,
            "model": self.model_uid,
            "dataset": self.dataset_uid,
            "results": self.results,
            "metadata": self.metadata,
            "approval_status": self.status.value,
            "approved_at": self.approved_at,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    def upload(self):
        """Uploads the results to the comms

        Args:
            comms (Comms): Instance of the communications interface.
        """
        results_info = self.todict()
        updated_results_info = config.comms.upload_results(results_info)
        return updated_results_info

    def write(self):
        # Remove any temporary cache associated to this result
        if self.tmp_path != self.path and os.path.exists(self.tmp_path):
            logging.debug("Moving result to permanent location")
            src = str(Path(self.tmp_path).parent)
            dst = str(Path(self.path).parent)
            if os.path.exists(dst):
                # Permanent version already exists, remove temporary
                rmtree(src)
            else:
                # Move temporary to permanent
                os.rename(src, dst)
        if os.path.exists(self.path):
            write_access = os.access(self.path, os.W_OK)
            logging.debug(f"file has write access? {write_access}")
            if not write_access:
                logging.debug("removing outdated and inaccessible results")
                os.remove(self.path)
        os.makedirs(Path(self.path).parent, exist_ok=True)
        with open(self.path, "w") as f:
            yaml.dump(self.todict(), f)

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
