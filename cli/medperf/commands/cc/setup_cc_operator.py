import json
from medperf.cc.config import check_operator_setup
from medperf.cc.operator import setup_operator
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
        check_operator_setup(cc_config)
        user = get_medperf_user_object()
        user.cc_operator.set(cc_config)
        body = {"metadata": user.metadata}
        config.comms.update_user(user.id, body)

        with config.ui.interactive():
            setup_operator(user)
            user.cc_operator.mark_initialized()
            body = {"metadata": user.metadata}
            config.comms.update_user(user.id, body)
