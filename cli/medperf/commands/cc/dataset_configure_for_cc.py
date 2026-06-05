from medperf.entities.dataset import Dataset
from medperf.asset_management.asset_management import (
    setup_dataset_for_cc,
    validate_cc_config,
)
import json
from medperf import config
from medperf.exceptions import InvalidEntityError


class DatasetConfigureForCC:
    @classmethod
    def run_from_files(cls, data_uid: int, cc_config_file: str, cc_policy_file: str):
        with open(cc_config_file) as f:
            cc_config = json.load(f)
        with open(cc_policy_file) as f:
            cc_policy = json.load(f)
        cls.run(data_uid, cc_config, cc_policy)

    @classmethod
    def run(cls, data_uid: int, cc_config: dict, cc_policy: dict):
        validate_cc_config(cc_config, "dataset" + str(data_uid))
        dataset = Dataset.get(data_uid)
        dataset.set_cc_config(cc_config)
        dataset.set_cc_policy(cc_policy)
        body = {"user_metadata": dataset.user_metadata}
        config.comms.update_dataset(dataset.id, body)
        with config.ui.interactive():
            config.ui.text = "Checking dataset hash"
            if not dataset.check_hash():
                raise InvalidEntityError(
                    "Dataset hash does not match the one stored in the system."
                )
            setup_dataset_for_cc(dataset)
            dataset.set_cc_initialized()
            body = {"user_metadata": dataset.user_metadata}
            config.comms.update_dataset(dataset.id, body)
