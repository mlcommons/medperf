import os
from medperf.entities.interface import Entity
from medperf.entities.schemas import ApprovableSchema
import medperf.config as config
from medperf.account_management import get_medperf_user_data
from typing import Optional
from datetime import datetime

from medperf.utils import remove_path
import yaml


class Execution(Entity, ApprovableSchema):
    """
    Class representing an Execution entry

    Executions are obtained after successfully running a benchmark
    execution flow. They contain information regarding the
    components involved in obtaining metrics results, as well as the
    results themselves. This class provides methods for working with
    benchmark executions and how to upload them to the backend.
    """

    benchmark: int
    model: int
    dataset: int
    results: dict = {}
    metadata: dict = {}
    user_metadata: dict = {}
    model_report: dict = {}
    evaluation_report: dict = {}
    finalized: bool = False
    finalized_at: Optional[datetime]

    @staticmethod
    def get_type():
        return "execution"

    @staticmethod
    def get_storage_path():
        return config.executions_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_execution

    @staticmethod
    def get_metadata_filename():
        return config.results_info_file

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_execution

    def __init__(self, *args, **kwargs):
        """Creates a new execution instance"""
        super().__init__(*args, **kwargs)
        self.results_path = os.path.join(self.path, config.results_filename)

    @property
    def local_id(self):
        return self.name

    def is_executed(self):
        flag_file = os.path.join(self.path, config.executed_flag)
        return os.path.exists(flag_file)

    def unmark_as_executed(self):
        flag_file = os.path.join(self.path, config.executed_flag)
        remove_path(flag_file)

    def mark_as_executed(self):
        flag_file = os.path.join(self.path, config.executed_flag)
        with open(flag_file, "w"):
            pass

    def save_results(self, results, partial):
        with open(self.results_path, "w") as f:
            yaml.safe_dump(results, f)

        if partial:
            flag_file = os.path.join(self.path, config.partial_flag)
            with open(flag_file, "w"):
                pass

    def read_results(self):
        with open(self.results_path) as f:
            results = yaml.safe_load(f)
        return results

    def is_partial(self):
        is_partial_from_metadata = self.metadata.get("partial", None)
        if is_partial_from_metadata is not None:
            return is_partial_from_metadata
        # otherwise, check locally
        flag_file = os.path.join(self.path, config.partial_flag)
        return os.path.exists(flag_file)

    @staticmethod
    def remote_prefilter(filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_executions
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_executions
            del filters["owner"]
        elif "benchmark" in filters and filters["benchmark"] is not None:
            # Only override the communications method if its not related to
            # the current user
            # This is needed so that users can filter their own executions
            # without getting permission errors.
            # Users will still be able to filter by benchmark through query params
            bmk = filters["benchmark"]
            del filters["benchmark"]

            def get_benchmark_executions(*args, **kwargs):
                # Decorate the benchmark results remote function so it has the same signature
                # as all the comms_fns
                return config.comms.get_benchmark_executions(bmk, *args, **kwargs)

            comms_fn = get_benchmark_executions

        return comms_fn

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
            "Finalized": self.finalized,
        }
