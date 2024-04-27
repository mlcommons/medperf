import hashlib
from typing import List, Union, Optional

import medperf.config as config
from medperf.entities.interface import Entity


class TestReport(Entity):
    """
    Class representing a compatibility test report entry

    A test report consists of the components of a test execution:
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

    @staticmethod
    def get_type():
        return "report"

    @staticmethod
    def get_storage_path():
        return config.tests_folder

    @staticmethod
    def get_metadata_filename():
        return config.test_report_file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = None
        self.for_test = True
        self.generated_uid = self.__generate_uid()

    def __generate_uid(self):
        """A helper that generates a unique hash for a test report."""
        params = self.todict()
        del params["results"]
        params = str(params)
        return hashlib.sha256(params.encode()).hexdigest()

    def set_results(self, results):
        self.results = results

    @classmethod
    def all(cls, unregistered: bool = False, filters: dict = {}) -> List["Entity"]:
        assert unregistered, "Reports are only unregistered"
        assert filters == {}, "Reports cannot be filtered"
        return super().all(unregistered=True, filters={})

    @classmethod
    def get(cls, report_uid: str, local_only: bool = False) -> "TestReport":
        return super().get(report_uid, local_only=True)

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
            "Model": (
                self.model if isinstance(self.model, int) else self.model[:27] + "..."
            ),
            "Evaluator": (
                self.data_evaluator_mlcube
                if isinstance(self.data_evaluator_mlcube, int)
                else self.data_evaluator_mlcube[:27] + "..."
            ),
        }
