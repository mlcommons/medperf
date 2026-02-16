from medperf.entities.dataset import Dataset
from medperf.exceptions import MedperfException
from medperf.asset_management.asset_management import update_dataset_cc_policy


class DatasetUpdateCCPolicy:
    @classmethod
    def run(cls, data_uid: int):
        dataset = Dataset.get(data_uid)
        if not dataset.is_cc_configured():
            raise MedperfException(
                f"Dataset {dataset.id} is not configured for confidential computing."
            )
        policy = {}
        update_dataset_cc_policy(dataset, policy)
