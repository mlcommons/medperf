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
        self.data_evaluator_mlcube = self._model.data_evaluator_mlcube
        self.metadata = self._model.metadata
        self.user_metadata = self._model.user_metadata
        self.is_active = self._model.is_active
        self.dataset_auto_approval_allow_list = (
            self._model.dataset_auto_approval_allow_list
        )
        self.dataset_auto_approval_mode = self._model.dataset_auto_approval_mode
        self.model_auto_approval_allow_list = self._model.model_auto_approval_allow_list
        self.model_auto_approval_mode = self._model.model_auto_approval_mode

    @property
    def local_id(self):
        return self.name

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
            approval_status=None,  # TODO
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
            "Data Evaluator Container": int(self.data_evaluator_mlcube),
            "State": self.state,
            "Approval Status": self.approval_status,
            "Registered": self.is_registered,
        }
