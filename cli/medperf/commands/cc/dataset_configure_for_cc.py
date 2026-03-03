from medperf.entities.dataset import Dataset
from medperf.asset_management.asset_management import setup_dataset_for_cc
import json
from medperf import config


class DatasetConfigureForCC:
    @classmethod
    def run(cls, data_uid: int, cc_config_file: str, cc_policy_file: str):
        dataset = Dataset.get(data_uid)
        with open(cc_config_file) as f:
            cc_config = json.load(f)
        with open(cc_policy_file) as f:
            cc_policy = json.load(f)
        dataset.set_cc_config(cc_config)
        dataset.set_cc_policy(cc_policy)
        body = {"user_metadata": dataset.user_metadata}
        config.comms.update_dataset(dataset.id, body)
        setup_dataset_for_cc(dataset)

        # mark as set
        dataset.mark_cc_configured()
        body = {"user_metadata": dataset.user_metadata}
        config.comms.update_dataset(dataset.id, body)
