from medperf.entities.interface import Entity
from medperf.entities.schemas import ApprovableSchema
import medperf.config as config
from medperf.account_management import get_medperf_user_data


class Result(Entity, ApprovableSchema):
    """
    Class representing a Result entry

    Results are obtained after successfully running a benchmark
    execution flow. They contain information regarding the
    components involved in obtaining metrics results, as well as the
    results themselves. This class provides methods for working with
    benchmark results and how to upload them to the backend.
    """

    benchmark: int
    model: int
    dataset: int
    results: dict
    metadata: dict = {}
    user_metadata: dict = {}

    @staticmethod
    def get_type():
        return "result"

    @staticmethod
    def get_storage_path():
        return config.results_folder

    @staticmethod
    def get_comms_retriever():
        return config.comms.get_result

    @staticmethod
    def get_metadata_filename():
        return config.results_info_file

    @staticmethod
    def get_comms_uploader():
        return config.comms.upload_result

    def __init__(self, *args, **kwargs):
        """Creates a new result instance"""
        super().__init__(*args, **kwargs)

        self.local_id = f"b{self.benchmark}m{self.model}d{self.dataset}"

    @classmethod
    def _Entity__remote_prefilter(cls, filters: dict) -> callable:
        """Applies filtering logic that must be done before retrieving remote entities

        Args:
            filters (dict): filters to apply

        Returns:
            callable: A function for retrieving remote entities with the applied prefilters
        """
        comms_fn = config.comms.get_results
        if "owner" in filters and filters["owner"] == get_medperf_user_data()["id"]:
            comms_fn = config.comms.get_user_results
        if "benchmark" in filters and filters["benchmark"] is not None:
            bmk = filters["benchmark"]

            def get_benchmark_results():
                # Decorate the benchmark results remote function so it has the same signature
                # as all the comms_fns
                return config.comms.get_benchmark_results(bmk)

            comms_fn = get_benchmark_results

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
        }
