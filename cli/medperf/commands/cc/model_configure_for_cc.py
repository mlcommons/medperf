from medperf.entities.model import Model
from medperf.asset_management.asset_management import setup_model_for_cc
import json
from medperf import config


class ModelConfigureForCC:
    @classmethod
    def run(cls, model_uid: int, cc_config_file: str, cc_policy_file: str):
        model = Model.get(model_uid)
        with open(cc_config_file) as f:
            cc_config = json.load(f)
        with open(cc_policy_file) as f:
            cc_policy = json.load(f)
        model.set_cc_config(cc_config)
        model.set_cc_policy(cc_policy)
        body = {"user_metadata": model.user_metadata}
        config.comms.update_model(model.id, body)
        setup_model_for_cc(model)
        # mark as set
        model.mark_cc_configured()
        body = {"user_metadata": model.user_metadata}
        config.comms.update_model(model.id, body)
