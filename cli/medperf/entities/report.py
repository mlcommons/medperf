import hashlib
import os
import yaml
import logging
from typing import List, Union, Optional

from medperf.utils import storage_path
from medperf.entities.schemas import MedperfBaseSchema
import medperf.config as config
from medperf.exceptions import InvalidArgumentError


class TestReport(MedperfBaseSchema):
    """
    Class representing a compatibility test report entry

    Results are obtained after successfully running a benchmark
    execution flow. They contain information regarding the
    components involved in obtaining metrics results, as well as the
    results themselves. This class provides methods for working with
    benchmark results and how to upload them to the backend.
    """

    demo_dataset_url: Optional[str]
    demo_dataset_hash: Optional[str]
    data_path: Optional[str]
    labels_path: Optional[str]
    prepared_data_hash: Optional[str]
    data_preparation_mlcube: Optional[Union[int, str]]
    model: Union[int, str]
    data_evaluator_mlcube: Union[int, str]
    results: Optional[dict]

    def __init__(self, *args, **kwargs):
        """Creates a new result instance"""
        super().__init__(*args, **kwargs)
        self.generate_uid()
        path = storage_path(config.test_storage)
        self.path = os.path.join(path, self.generated_uid)

    def generate_uid(self):
        params = self.todict()
        del params["results"]
        params = str(params)
        self.generated_uid = hashlib.sha1(params.encode()).hexdigest()

    def set_results(self, results):
        self.results = results

    def cached_results(self):
        """checks the existance of, and retrieves if possible, the compatibility test
        result. This method is called prior to the test execution.

        Returns:
            (dict|None): None if the result does not exist or if self.no_cache is True,
            otherwise it returns the found result.
        """
        try:
            report = self.__class__.__get_local_dict(self.generated_uid)
            logging.info(f"Existing results at {self.path} were detected.")
            logging.info("The compatibilty test will not be re-executed.")
            return report
        except InvalidArgumentError:
            pass

    @classmethod
    def all(
        cls, local_only: bool = False, mine_only: bool = False
    ) -> List["TestReport"]:
        """Gets and creates instances of all the user's results

        Args:
            local_only (bool, optional): Wether to retrieve only local entities. Defaults to False.
            mine_only (bool, optional): Wether to retrieve only current-user entities. Defaults to False.

        Returns:
            List[Result]: List containing all results
        """
        logging.info("Retrieving all reports")
        reports = []
        test_storage = storage_path(config.test_storage)
        try:
            uids = next(os.walk(test_storage))[1]
        except StopIteration:
            msg = "Couldn't iterate over the tests directory"
            logging.warning(msg)
            raise RuntimeError(msg)

        for uid in uids:
            local_meta = cls.__get_local_dict(uid)
            report = cls(**local_meta)
            reports.append(report)

        return reports

    @classmethod
    def get(cls, report_uid: Union[str, int]) -> "TestReport":
        """Retrieves and creates a Result instance obtained from the platform.
        If the result instance already exists in the user's machine, it loads
        the local instance

        Args:
            report_uid (str): UID of the Result instance

        Returns:
            Result: Specified Result instance
        """
        logging.debug(f"Retrieving report {report_uid}")
        report_dict = cls.__get_local_dict(report_uid)
        report = cls(**report_dict)
        report.write()
        return report

    def todict(self):
        return self.extended_dict()

    def write(self):
        report_file = os.path.join(self.path, config.test_report_file)
        if os.path.exists(report_file):
            write_access = os.access(report_file, os.W_OK)
            logging.debug(f"file has write access? {write_access}")
            if not write_access:
                logging.debug("removing outdated and inaccessible results")
                os.remove(report_file)
        os.makedirs(self.path, exist_ok=True)
        with open(report_file, "w") as f:
            yaml.dump(self.todict(), f)
        return report_file

    @classmethod
    def __get_local_dict(cls, local_uid):
        report_path = os.path.join(storage_path(config.test_storage), str(local_uid))
        report_file = os.path.join(report_path, config.test_report_file)
        if not os.path.exists(report_file):
            raise InvalidArgumentError(
                f"The requested report {local_uid} could not be retrieved"
            )
        with open(report_file, "r") as f:
            report_info = yaml.safe_load(f)
        return report_info

    def display_dict(self):
        if self.data_path:
            data_source = f"{self.data_path}"[:27] + "..."
        elif self.demo_dataset_url:
            data_source = f"{self.demo_dataset_url}"[:27] + "..."
        else:
            data_source = f"{self.prepared_data_hash}"

        return {
            "UID": self.generated_uid,
            "Data Source": data_source,
            "Model": self.model
            if isinstance(self.model, int)
            else self.model[:27] + "...",
            "Evaluator": self.data_evaluator_mlcube
            if isinstance(self.data_evaluator_mlcube, int)
            else self.data_evaluator_mlcube[:27] + "...",
        }
