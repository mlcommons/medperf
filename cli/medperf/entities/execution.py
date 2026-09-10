import os
from medperf.entities.interface import Entity
from medperf.entities.schemas import ExecutionSchema
import medperf.config as config
from medperf.account_management import get_medperf_user_data
from medperf.utils import remove_path
import yaml
from medperf.entities.utils import handle_validation_error


class Execution(Entity):
    """
    Class representing an Execution entry

    Executions are obtained after successfully running a benchmark
    execution flow. They contain information regarding the
    components involved in obtaining metrics results, as well as the
    results themselves. This class provides methods for working with
    benchmark executions and how to upload them to the backend.
    """

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

    @handle_validation_error
    def __init__(self, **kwargs):
        """Creates a new execution instance"""
        self._model = ExecutionSchema(**kwargs)
        super().__init__()
        self.approved_at = self._model.approved_at
        self.approval_status = self._model.approval_status
        self.benchmark = self._model.benchmark
        self.model = self._model.model
        self.dataset = self._model.dataset
        self.results = self._model.results
        self.metadata = self._model.metadata
        self.user_metadata = self._model.user_metadata
        self.model_report = self._model.model_report
        self.evaluation_report = self._model.evaluation_report
        self.integrity_proof = self._model.integrity_proof
        self.finalized = self._model.finalized
        self.finalized_at = self._model.finalized_at

        self._set_helper_attributes()

    def _set_helper_attributes(self):
        self.results_path = os.path.join(self.path, config.results_filename)
        self.integrity_proof_path = os.path.join(
            self.path, config.integrity_proof_filename
        )
        self.local_outputs_path = os.path.join(self.path, config.local_metrics_outputs)

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

    def save_results(self, results, partial, integrity_proof=None):
        with open(self.results_path, "w") as f:
            yaml.safe_dump(results, f)

        if integrity_proof:
            self.integrity_proof = integrity_proof
            with open(self.integrity_proof_path, "w") as f:
                yaml.safe_dump(integrity_proof, f)

        if partial:
            flag_file = os.path.join(self.path, config.partial_flag)
            with open(flag_file, "w"):
                pass

    def read_integrity_proof(self):
        """What the workload attested about these results, if it produced one.

        Written beside the results when they were collected. Read back here so
        that reporting the results reports the proof with them -- otherwise
        only whoever collected them could ever check it."""
        if self.integrity_proof:
            return self.integrity_proof
        if not os.path.exists(self.integrity_proof_path):
            return {}
        with open(self.integrity_proof_path) as f:
            return yaml.safe_load(f) or {}

    def read_results(self):
        if self.finalized:
            return self.results
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
        elif "dataset" in filters and filters["dataset"] is not None:
            # A dataset owner's own listing leaves out an execution somebody
            # else operated on their data -- it belongs to whoever ran it. The
            # dataset-scoped listing is the one that shows them all of them.
            dataset = filters["dataset"]
            del filters["dataset"]

            def get_dataset_executions(*args, **kwargs):
                # Decorate the dataset results remote function so it has the same signature
                # as all the comms_fns
                return config.comms.get_dataset_executions(dataset, *args, **kwargs)

            comms_fn = get_dataset_executions

        return comms_fn

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Benchmark": self.benchmark,
            "Model": self.model,
            "Dataset": self.dataset,
            "Partial": self.metadata.get("partial", "N/A"),
            "Executed": self.is_executed(),
            "Approval Status": self.approval_status,
            "Created At": self.created_at,
            "Registered": self.is_registered,
            "Finalized": self.finalized,
        }
