import json
from medperf.asset_management.asset_management import setup_operator
from medperf.account_management import get_medperf_user_object
from medperf import config


class SetupCCOperator:
    @classmethod
    def run(cls, cc_config_file: str):
        user = get_medperf_user_object()
        if user.is_cc_configured():
            raise ValueError(
                "User already has a configured confidential computing operator."
            )
        with open(cc_config_file) as f:
            cc_config = json.load(f)

        user.set_cc_config(cc_config)
        body = {"metadata": user.metadata}
        config.comms.update_user(user.id, body)
        setup_operator(user)

        # mark as set
        user.mark_cc_configured()
        body = {"metadata": user.metadata}
        config.comms.update_user(user.id, body)
