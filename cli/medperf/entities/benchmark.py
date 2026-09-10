from typing import List
from medperf.commands.association.utils import (
    get_experiment_associations,
    get_user_associations,
)

import medperf.config as config
from medperf.entities.interface import Entity
from medperf.entities.schemas import BenchmarkSchema
from medperf.account_management import get_medperf_user_data
from medperf.entities.utils import handle_validation_error
from medperf.enums import BenchmarkTopology


class Benchmark(Entity):
    """
    Class representing a Benchmark

    a benchmark is a bundle of assets that enables quantitative
    measurement of the performance of AI models for a specific
    clinical problem. A Benchmark instance contains information
    regarding how to prepare datasets for execution, as well as
    what models to run and how to evaluate them.
    """

    @staticmethod
    def get_type():
        return "benchmark"

    @staticmethod
    def get_storage_path():
        return config.benchmarks_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_benchmark

    @staticmethod
    def get_metadata_filename():
        return config.benchmarks_filename

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_benchmark

    @staticmethod
    def get_comms_counter():
        return config.comms.get_benchmarks_count

    @handle_validation_error
    def __init__(self, **kwargs):
        """Creates a new benchmark instance

        Args:
            bmk_desc (Union[dict, BenchmarkModel]): Benchmark instance description
        """
        self._model = BenchmarkSchema(**kwargs)
        super().__init__()
        self.state = self._model.state
        self.approved_at = self._model.approved_at
        self.approval_status = self._model.approval_status
        self.description = self._model.description
        self.docs_url = self._model.docs_url
        self.demo_dataset_tarball_url = self._model.demo_dataset_tarball_url
        self.demo_dataset_tarball_hash = self._model.demo_dataset_tarball_hash
        self.demo_dataset_generated_uid = self._model.demo_dataset_generated_uid
        self.data_preparation_mlcube = self._model.data_preparation_mlcube
        self.reference_model = self._model.reference_model
        self.topology = self._model.topology
        self.data_evaluator_mlcube = self._model.data_evaluator_mlcube
        self.benchmark_script = self._model.benchmark_script
        self.metadata = self._model.metadata
        self.user_metadata = self._model.user_metadata
        self.is_active = self._model.is_active
        self.dataset_auto_approval_allow_list = (
            self._model.dataset_auto_approval_allow_list
        )
        self.dataset_auto_approval_mode = self._model.dataset_auto_approval_mode
        self.model_auto_approval_allow_list = self._model.model_auto_approval_allow_list
        self.model_auto_approval_mode = self._model.model_auto_approval_mode
        self.committee_member_emails = self._model.committee_member_emails

    def user_can_manage(self, user_data=None):
        user_data = user_data or get_medperf_user_data()
        if self.owner == user_data["id"]:
            return True

        user_email = user_data["email"].lower()
        committee_emails = [email.lower() for email in self.committee_member_emails]
        if user_email in committee_emails:
            return True
        return False

    @property
    def local_id(self):
        return self.name

    @property
    def topology_enum(self) -> BenchmarkTopology:
        """The benchmark's topology as an enum. `self.topology` is the raw
        string, since the underlying schema is configured with `use_enum_values`."""
        return BenchmarkTopology(self.topology)

    @staticmethod
    def remote_prefilter(filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_benchmarks
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_benchmarks
        return comms_fn

    @classmethod
    def get_models_uids(cls, benchmark_uid: int) -> List[int]:
        """Retrieves the list of models associated to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.

        Returns:
            List[int]: List of mlcube uids
        """
        associations = get_experiment_associations(
            experiment_id=benchmark_uid,
            experiment_type="benchmark",
            component_type="model",
            approval_status="APPROVED",
        )
        models_uids = [assoc["model"] for assoc in associations]
        return models_uids

    @classmethod
    def get_datasets_uids(cls, benchmark_uid: int) -> List[int]:
        """Retrieves the list of datasets associated to the benchmark

        Readable by the benchmark's owner, its committee, and the model owners
        taking part: it is what tells a model owner which datasets there are to
        run against.

        Args:
            benchmark_uid (int): UID of the benchmark.

        Returns:
            List[int]: List of dataset uids
        """
        associations = get_experiment_associations(
            experiment_id=benchmark_uid,
            experiment_type="benchmark",
            component_type="dataset",
            approval_status="APPROVED",
        )
        datasets_uids = [assoc["dataset"] for assoc in associations]
        return datasets_uids

    @classmethod
    def get_datasets_with_users(cls, benchmark_uid: int) -> List[dict]:
        """Retrieves the list of datasets and their owner info, associated to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.

        Returns:
            List[dict]: List of dicts of dataset IDs with their owner info
        """
        uids_with_users = config.comms.get_benchmark_datasets_with_users(benchmark_uid)
        return uids_with_users

    @classmethod
    def get_models_associations(cls, benchmark_uid: int) -> List[dict]:
        """Retrieves the list of model associations to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.

        Returns:
            List[dict]: List of associations
        """

        experiment_type = "benchmark"
        component_type = "model"

        associations = get_user_associations(
            experiment_type=experiment_type,
            component_type=component_type,
            approval_status=None,
        )

        associations = [a for a in associations if a["benchmark"] == benchmark_uid]

        return associations

    @classmethod
    def get_datasets_associations(cls, benchmark_uid: int) -> List[dict]:
        """Retrieves the list of models associated to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.

        Returns:
            List[dict]: List of associations
        """

        experiment_type = "benchmark"
        component_type = "dataset"

        associations = get_user_associations(
            experiment_type=experiment_type,
            component_type=component_type,
            approval_status=None,
        )

        associations = [a for a in associations if a["benchmark"] == benchmark_uid]

        return associations

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Description": self.description,
            "Documentation": self.docs_url,
            "Created At": self.created_at,
            "Data Preparation Container": int(self.data_preparation_mlcube),
            "Reference Model": int(self.reference_model),
            "Topology": self.topology,
            "Data Evaluator Container": (
                int(self.data_evaluator_mlcube)
                if self.data_evaluator_mlcube is not None
                else "N/A"
            ),
            "Benchmark Script": (
                int(self.benchmark_script)
                if self.benchmark_script is not None
                else "N/A"
            ),
            "State": self.state,
            "Approval Status": self.approval_status,
            "Registered": self.is_registered,
        }
