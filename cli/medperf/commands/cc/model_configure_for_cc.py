from medperf.entities.model import Model
from medperf.cc.assets import setup_model_for_cc
from medperf.cc.config import check_asset_setup
import json
from medperf import config
from medperf.exceptions import InvalidEntityError
from medperf_cc import AssetKind


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
        check_asset_setup(cc_config, cc_policy, model, AssetKind.MODEL)
        model.set_cc_config(cc_config)
        model.set_cc_policy(cc_policy)
        body = {"user_metadata": model.user_metadata}
        config.comms.update_model(model.id, body)
        with config.ui.interactive():
            config.ui.text = "Checking model hash"
            if not model.check_hash():
                raise InvalidEntityError(
                    "Model hash does not match the one stored in the system."
                )
            setup_model_for_cc(model)
            model.set_cc_initialized()
            body = {"user_metadata": model.user_metadata}
            config.comms.update_model(model.id, body)
