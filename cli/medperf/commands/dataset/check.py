from medperf.entities.dataset import Dataset
from medperf.account_management.account_management import get_medperf_user_data
from medperf.exceptions import InvalidArgumentError
from medperf import config


class DataCheck:
    @staticmethod
    def run(dataset_uid: int):
        dataset = Dataset.get(dataset_uid)
        user_id = get_medperf_user_data()["id"]
        if dataset.owner != user_id:
            raise InvalidArgumentError("Only the dataset owner can check the hash.")
        if dataset.check_hash():
            config.ui.print("✅ Data hash matches the one registered on the server.")
        else:
            config.ui.print(
                "❌ Data hash does not match the one registered on the server."
            )
