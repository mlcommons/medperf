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

    Note: This entity is only a local one, there is no TestReports on the server
          However, we still use the same Entity interface used by other entities
          in order to reduce repeated code. Consequently, we mocked a few methods
          and attributes inherited from the Entity interface that are not relevant to
          this entity, such as the `name` and `id` attributes, and such as
          the `get` and `all` methods.
    """

    name: Optional[str] = "name"
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

    @property
    def local_id(self):
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
    def get(cls, uid: str, local_only: bool = False) -> "TestReport":
        """Gets an instance of the TestReport. ignores local_only inherited flag as TestReport is always a local entity.
        Args:
            uid (str): Report Unique Identifier
            local_only (bool): ignored. Left for aligning with parent Entity class
        Returns:
            TestReport: Report Instance associated to the UID
        """
        return super().get(uid, local_only=True)

    def display_dict(self):
        if self.data_path:
            data_source = f"{self.data_path}"[:27] + "..."
        elif self.demo_dataset_url:
            data_source = f"{self.demo_dataset_url}"[:27] + "..."
        else:
            data_source = f"{self.prepared_data_hash}"

        return {
            "UID": self.local_id,
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
