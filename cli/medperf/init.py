import os

from medperf import config
from medperf.comms.factory import CommsFactory
from medperf.config_management import setup_config
from medperf.logging import setup_logging
from medperf.storage import (
    apply_configuration_migrations,
    init_storage,
    override_storage_config_paths,
)
from medperf.ui.factory import UIFactory


def initialize():
    # Apply any required migration
    apply_configuration_migrations()

    # setup config
    setup_config()

    # Initialize storage
    override_storage_config_paths()
    init_storage()

    # Setup logging
    log_file = os.path.join(config.logs_storage, config.log_file)
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
