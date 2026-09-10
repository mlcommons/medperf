import json

from medperf import config
from medperf.account_management import get_medperf_user_object
from medperf.cc.config import check_collector_setup
from medperf.cc.results import setup_collector


class SetupCCCollector:
    """Records where this user receives the results of confidential runs.

    Separate from the operator settings because the two are separate roles.
    Whoever runs the workload needs a machine; whoever the results are for
    needs somewhere to receive them, and the workload writes there rather than
    anywhere the operator owns."""

    @classmethod
    def run_from_files(cls, cc_config_file: str):
        with open(cc_config_file) as f:
            cc_config = json.load(f)
        cls.run(cc_config)

    @classmethod
    def run(cls, cc_config: dict):
        check_collector_setup(cc_config)
        user = get_medperf_user_object()
        user.cc_collector.set(cc_config)
        config.comms.update_user(user.id, {"metadata": user.metadata})

        with config.ui.interactive():
            setup_collector(user)
            user.cc_collector.mark_initialized()
            config.comms.update_user(user.id, {"metadata": user.metadata})
