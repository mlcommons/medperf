from typing import List, Optional
from pydantic import HttpUrl, Field

from medperf import settings
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
        return settings.benchmarks_folder

    @staticmethod
    def get_comms_retriever():
        return settings.comms.get_benchmark

    @staticmethod
    def get_metadata_filename():
        return settings.benchmarks_filename

    @staticmethod
    def get_comms_uploader():
        return settings.comms.upload_benchmark

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
        comms_fn = settings.comms.get_benchmarks
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = settings.comms.get_user_benchmarks
        return comms_fn

    @classmethod
    def get_models_uids(cls, benchmark_uid: int) -> List[int]:
        """Retrieves the list of models associated to the benchmark

        Args:
            benchmark_uid (int): UID of the benchmark.
            comms (Comms): Instance of the communications interface.

        Returns:
            List[int]: List of mlcube uids
        """
        associations = settings.comms.get_benchmark_model_associations(benchmark_uid)
        models_uids = [
            assoc["model_mlcube"]
            for assoc in associations
            if assoc["approval_status"] == "APPROVED"
        ]
        return models_uids

    def display_dict(self):
        return {
            "UID": self.identifier,
            "Name": self.name,
            "Description": self.description,
            "Documentation": self.docs_url,
            "Created At": self.created_at,
            "Data Preparation MLCube": int(self.data_preparation_mlcube),
            "Reference Model MLCube": int(self.reference_model_mlcube),
            "Data Evaluator MLCube": int(self.data_evaluator_mlcube),
            "State": self.state,
            "Approval Status": self.approval_status,
            "Registered": self.is_registered,
        }
