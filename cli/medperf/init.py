import os
from medperf.config_management import setup_config
from medperf.storage import override_storage_config_paths, init_storage
from medperf.logging import setup_logging
from medperf.ui.factory import UIFactory
from medperf.comms.factory import CommsFactory
from medperf import config


def initialize():
    # setup config
    setup_config()

    # Initialize storage
    override_storage_config_paths()
    init_storage()

    # Setup logging
    log_file = os.path.join(config.logs_folder, config.log_file)
    setup_logging(log_file, config.loglevel)

    # Setup UI, COMMS
    config.ui = UIFactory.create_ui(config.ui)
    config.comms = CommsFactory.create_comms(config.comms, config.server)

    # Setup auth class
    if config.auth_class == "Auth0":
        from .comms.auth import Auth0

        config.auth = Auth0()
    elif config.auth_class == "Local":
        from .comms.auth import Local

        config.auth = Local()
    else:
        raise ValueError(f"Unknown Auth class {config.auth_class}")
