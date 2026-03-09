from medperf.entities.model import Model
from medperf.asset_management.asset_management import setup_model_for_cc
import json
from medperf import config


class ModelConfigureForCC:
    @classmethod
    def run_from_files(cls, model_uid: int, cc_config_file: str, cc_policy_file: str):
        with open(cc_config_file) as f:
            cc_config = json.load(f)
        with open(cc_policy_file) as f:
            cc_policy = json.load(f)
        cls.run(model_uid, cc_config, cc_policy)

    @classmethod
    def run(cls, model_uid: int, cc_config: dict, cc_policy: dict):
        model = Model.get(model_uid)
        model.set_cc_config(cc_config)
        model.set_cc_policy(cc_policy)
        setup_model_for_cc(model)
        body = {"user_metadata": model.user_metadata}
        config.comms.update_model(model.id, body)
