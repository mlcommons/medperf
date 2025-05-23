from typing import List, Optional
from medperf.commands.association.utils import (
    get_experiment_associations,
    get_user_associations,
)
from pydantic import HttpUrl, Field

import medperf.config as config
from medperf.entities.association import Association
from medperf.entities.interface import Entity
from medperf.entities.schemas import ApprovableSchema, DeployableSchema
from medperf.account_management import get_medperf_user_data


class Benchmark(Entity, ApprovableSchema, DeployableSchema):
    """
    Class representing a Benchmark

    a benchmark is a bundle of assets that enables quantitative
    measurement of the performance of AI models for a specific
    clinical problem. A Benchmark instance contains information
    regarding how to prepare datasets for execution, as well as
    what models to run and how to evaluate them.
    """

    description: Optional[str] = Field(None, max_length=20)
    docs_url: Optional[HttpUrl]
    demo_dataset_tarball_url: str
    demo_dataset_tarball_hash: Optional[str]
    demo_dataset_generated_uid: Optional[str]
    data_preparation_mlcube: int
    reference_model_mlcube: int
    data_evaluator_mlcube: int
    metadata: dict = {}
    user_metadata: dict = {}
    is_active: bool = True

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

    def __init__(self, *args, **kwargs):
        """Creates a new benchmark instance

        Args:
            bmk_desc (Union[dict, BenchmarkModel]): Benchmark instance description
        """
        super().__init__(*args, **kwargs)

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
            component_type="model_mlcube",
            approval_status="APPROVED",
        )
        models_uids = [assoc["model_mlcube"] for assoc in associations]
        return models_uids

    @classmethod
    def get_models_associations(cls, benchmark_uid: int) -> List[Association]:
        """Retrieves the list of model associations to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.

        Returns:
            List[Association]: List of associations
        """

        experiment_type = "benchmark"
        component_type = "model_mlcube"

        associations = get_user_associations(
            experiment_type=experiment_type,
            component_type=component_type,
            approval_status=None,
        )

        associations = [Association(**assoc) for assoc in associations]
        associations = [a for a in associations if a.benchmark == benchmark_uid]

        return associations

    @classmethod
    def get_datasets_associations(cls, benchmark_uid: int) -> List[Association]:
        """Retrieves the list of models associated to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.

        Returns:
            List[Association]: List of associations
        """

        experiment_type = "benchmark"
        component_type = "dataset"

        associations = get_user_associations(
            experiment_type=experiment_type,
            component_type=component_type,
            approval_status=None,
        )

        associations = [Association(**assoc) for assoc in associations]
        associations = [a for a in associations if a.benchmark == benchmark_uid]

        return associations

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Description": self.description,
            "Documentation": self.docs_url,
            "Created At": self.created_at,
            "Data Preparation Container": int(self.data_preparation_mlcube),
            "Reference Model Container": int(self.reference_model_mlcube),
            "Data Evaluator Container": int(self.data_evaluator_mlcube),
            "State": self.state,
            "Approval Status": self.approval_status,
            "Registered": self.is_registered,
        }
