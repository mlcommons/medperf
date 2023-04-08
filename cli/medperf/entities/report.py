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

    A test report is comprised of the components of a test execution:
    - data used, which can be:
        - a demo dataset url and its hash, or
        - a raw data path and its labels path, or
        - a prepared dataset uid
    - Data preparation cube if the data used was not already prepared
    - model cube
    - evaluator cube
    - results
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
        super().__init__(*args, **kwargs)
        self.generated_uid = self.__generate_uid()
        path = storage_path(config.test_storage)
        self.path = os.path.join(path, self.generated_uid)

    def __generate_uid(self):
        """A helper that generates a unique hash for a test report."""
        params = self.todict()
        del params["results"]
        params = str(params)
        return hashlib.sha1(params.encode()).hexdigest()

    def set_results(self, results):
        self.results = results

    @classmethod
    def all(
        cls, local_only: bool = False, mine_only: bool = False
    ) -> List["TestReport"]:
        """Gets and creates instances of test reports.
        Arguments are only specified for compatibility with
        `Entity.List` and `Entity.View`, but they don't contribute to
        the logic.

        Returns:
            List[TestReport]: List containing all test reports
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
    def get(cls, report_uid: str) -> "TestReport":
        """Retrieves and creates a TestReport instance obtained the user's machine

        Args:
            report_uid (str): UID of the TestReport instance

        Returns:
            TestReport: Specified TestReport instance
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
