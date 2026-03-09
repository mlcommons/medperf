import json
from medperf.asset_management.asset_management import (
    setup_operator,
    validate_cc_operator_config,
)
from medperf.account_management import get_medperf_user_object
from medperf import config


class SetupCCOperator:
    @classmethod
    def run_from_files(cls, cc_config_file: str):
        with open(cc_config_file) as f:
            cc_config = json.load(f)
        cls.run(cc_config)

    @classmethod
    def run(cls, cc_config: dict):
        validate_cc_operator_config(cc_config)
        user = get_medperf_user_object()
        user.set_cc_config(cc_config)
        setup_operator(user)
        body = {"metadata": user.metadata}
        config.comms.update_user(user.id, body)
