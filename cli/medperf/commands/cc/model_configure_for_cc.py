from medperf.entities.model import Model
from medperf.asset_management.asset_management import (
    setup_model_for_cc,
    validate_cc_config,
)
import json
from medperf import config
from medperf.exceptions import InvalidEntityError


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
        validate_cc_config(cc_config, "model" + str(model_uid))
        model = Model.get(model_uid)
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
