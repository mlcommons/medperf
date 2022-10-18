import os
from medperf.enums import Status
import yaml
import logging
from typing import List

from medperf.utils import (
    results_ids,
    results_path,
)
from medperf.entities.interface import Entity
import medperf.config as config


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

        self.path = results_path(self.benchmark_uid, self.model_uid, self.dataset_uid)
        self.path = os.path.join(self.path, config.results_info_file)

    @classmethod
    def from_entities_uids(
        cls, benchmark_uid: str, dataset_uid: str, model_uid: str
    ) -> "Result":
        path = results_path(benchmark_uid, model_uid, dataset_uid)
        path = os.path.join(path, config.results_info_file)
        with open(path, "r") as f:
            results_info = yaml.safe_load(f)
        return cls(results_info)

    @classmethod
    def all(cls) -> List["Result"]:
        """Gets and creates instances of all the user's results
        """
        logging.info("Retrieving all results")
        results_ids_tuple = results_ids()
        results = []
        for result_ids in results_ids_tuple:
            b_id, m_id, d_id = result_ids
            results.append(cls.from_entities_uids(b_id, d_id, m_id))

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
        local_result = list(
            filter(lambda res: str(res.uid) == str(result_uid), cls.all())
        )
        if len(local_result) == 1:
            logging.debug("Found result locally")
            return local_result[0]

        meta = comms.get_result(result_uid)
        result = cls(meta)
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

        self.uid = updated_results_info["id"]
        self.owner = updated_results_info["owner"]
        self.created_at = updated_results_info["created_at"]
        self.modified_at = updated_results_info["modified_at"]

        self.write()

    def write(self):
        if os.path.exists(self.path):
            write_access = os.access(self.path, os.W_OK)
            logging.debug(f"file has write access? {write_access}")
            if not write_access:
                logging.debug("removing outdated and inaccessible results")
                os.remove(self.path)
        with open(self.path, "w") as f:
            yaml.dump(self.todict(), f)
