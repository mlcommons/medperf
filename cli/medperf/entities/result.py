import os
from medperf.enums import Status
import yaml
import logging
from typing import List

from medperf.utils import (
    storage_path,
    results_ids,
    results_path,
)
from medperf.entities.interface import Entity
import medperf.config as config
from medperf.comms.interface import Comms


class Result(Entity):
    """
    Class representing a Result entry

    Results are obtained after successfully running a benchmark
    execution flow. They contain information regarding the
    components involved in obtaining metrics results, as well as the
    results themselves. This class provides methods for working with
    benchmark results and how to upload them to the backend.
    """

    def __init__(
        self, benchmark_uid: str, dataset_uid: str, model_uid: str, results: dict = None
    ):
        """Creates a new result instance

        Args:
            benchmark_uid (str): UID of the executed benchmark.
            dataset_uid (str): UID of the dataset used.
            model_uid (str): UID of the model used.
            results()
        """
        self.path = results_path(benchmark_uid, model_uid, dataset_uid)
        self.benchmark_uid = benchmark_uid
        self.dataset_uid = dataset_uid
        self.model_uid = model_uid
        self.status = Status.PENDING
        self.results = results
        if self.results is None:
            self.results = {}
            self.get_results()
        self.uid = self.results.get("uid", None)

    @classmethod
    def all(cls) -> List["Result"]:
        """Gets and creates instances of all the user's results
        """
        logging.info("Retrieving all results")
        results_ids_tuple = results_ids(config.ui)
        storage_path(config.results_storage)
        results = []
        for result_ids in results_ids_tuple:
            b_id, m_id, d_id = result_ids
            results.append(cls(b_id, d_id, m_id))

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
        bmk_uid = meta["benchmark"]
        dset_uid = meta["dataset"]
        model_uid = meta["model"]
        result_data = meta["results"]

        return cls(bmk_uid, dset_uid, model_uid, result_data)

    def todict(self):
        result_dict = {
            "name": f"{self.benchmark_uid}_{self.model_uid}_{self.dataset_uid}",
            "results": self.results,
            "metadata": {},
            "approval_status": self.status.value,
            "benchmark": self.benchmark_uid,
            "model": self.model_uid,
            "dataset": self.dataset_uid,
        }
        return result_dict

    def upload(self, comms: Comms):
        """Uploads the results to the comms

        Args:
            comms (Comms): Instance of the communications interface.
        """
        result_uid = comms.upload_results(self.todict())
        self.uid = result_uid
        self.results["uid"] = result_uid
        self.set_results()

    def set_results(self):
        write_access = os.access(self.path, os.W_OK)
        logging.debug(f"file has write access? {write_access}")
        if not write_access:
            logging.debug("removing outdated and inaccessible results")
            os.remove(self.path)
        with open(self.path, "w") as f:
            yaml.dump(self.results, f)

    def get_results(self):
        with open(self.path, "r") as f:
            self.results = yaml.safe_load(f)
